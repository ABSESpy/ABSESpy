#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
The spatial module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Type

from loguru import logger
from mesa_geo import GeoSpace

from abses._bases.modules import CompositeModule, HowCreation
from abses.patch import CRS, PatchModule, _PatchModuleFactory

if TYPE_CHECKING:
    from abses.main import MainModel


class BaseNature(CompositeModule, GeoSpace):
    """Base class for managing spatial components in an ABSESpy model.

    This class serves as a container for different raster layers (PatchModules).
    It is not a raster layer itself, but manages multiple PatchModule instances.

    Attributes:
        major_layer: Primary raster layer of the model. Defaults to first created layer.
        total_bounds: Spatial extent of the model's area of interest.
        crs: Coordinate Reference System used by the nature module.
        layers: Collection of all managed raster layers.
        modules: Factory for creating and managing PatchModules.

    Note:
        By default, an initialized ABSESpy model will create an instance of BaseNature
        as its 'nature' module.
    """

    def __init__(
        self, model: MainModel[Any, Any], name: str = "nature"
    ) -> None:
        """Initializes a new BaseNature instance.

        Args:
            model: Parent model instance this nature module belongs to.
            name: Name identifier for this module (defaults to "nature").
        """
        CompositeModule.__init__(self, model, name=name)
        GeoSpace.__init__(self, crs=CRS)
        self._major_layer: Optional[PatchModule] = None
        self._modules: _PatchModuleFactory = _PatchModuleFactory(self)

    def __repr__(self) -> str:
        major_layer = (
            self.major_layer.name
            if self.major_layer is not None
            else "No major"
        )
        flag = "open" if self.opening else "closed"
        return f"<nature ({major_layer}): {flag}>"

    def __getattr__(self, name: str) -> Any:
        """Delegates attribute access to major_layer when not found in BaseNature.

        Args:
            name: Name of the attribute being accessed.

        Returns:
            Value of the attribute from major_layer.

        Raises:
            AttributeError: If no major layer is set or attribute not found.
        """
        if name.startswith("_"):
            return super().__getattribute__(name)
        if self._major_layer is None:
            raise AttributeError(f"No major layer set and {name} not found")
        return getattr(self._major_layer, name)

    @property
    def major_layer(self) -> Optional[PatchModule]:
        """Primary raster layer of the nature module.

        Returns:
            The current major layer, or None if not set.
        """
        return self._major_layer

    @major_layer.setter
    def major_layer(self, layer: PatchModule) -> None:
        """Sets the major layer for this nature module.

        Args:
            layer: PatchModule instance to set as major layer.

        Raises:
            TypeError: If layer is not a PatchModule instance.

        Note:
            If the layer has a CRS different from nature's current CRS,
            nature's CRS will be updated to match.
        """
        if not isinstance(layer, PatchModule):
            raise TypeError(f"{layer} is not PatchModule.")
        self._major_layer = layer
        if layer.crs is None:
            logger.warning("Setting major layer's CRS is None.")
        elif not self.layers:
            self.to_crs(layer.crs)
            logger.warning(
                f"the nature's CRS has been changed to {layer.crs}."
            )

    def create_module(
        self,
        module_cls: Optional[Type[PatchModule]] = None,
        how: Optional[HowCreation] = None,
        major_layer: bool = False,
        write_crs: bool = True,
        **kwargs: Any,
    ) -> PatchModule:
        """Creates a new raster layer (PatchModule) in this nature module.

        Args:
            module_cls: Custom PatchModule subclass to instantiate. If None, uses base PatchModule.
            how: Method to use for creating the layer. Options:
                - "from_resolution": Create by specifying shape and resolution
                - "from_file": Create from a geo-tiff dataset
                - "copy_layer": Copy properties from existing layer
                If None, creates basic module without special initialization.
            major_layer: If True, sets created module as the major layer.
            write_crs: If True, assigns nature's CRS to module if module's CRS is None.
            **kwargs: Additional arguments passed to the creation method.

        Returns:
            Newly created PatchModule instance.

        Note:
            The first created module automatically becomes the major layer.
            The module is automatically added to nature's layers collection.
        """
        if self.modules.is_empty:
            major_layer = True
        module = self.modules.new(how=how, module_class=module_cls, **kwargs)
        # 如果是第一个创建的模块,则将其作为主要的图层
        if major_layer:
            self.major_layer = module
        if write_crs and module.crs is None:
            logger.warning(
                f"{module.name}'s default CRS is None."
                f"Setting it to nature's CRS {self.crs}.",
            )
            module.crs = self.crs
        setattr(self, module.name, module)
        self.add_layer(module)
        return module
