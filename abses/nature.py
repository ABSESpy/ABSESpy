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

import numpy as np
import pyproj

from abses._bases.modules import CompositeModule, HowCreation
from abses.patch import CRS, PatchModule, _PatchModuleFactory

if TYPE_CHECKING:
    from abses.main import MainModel


class BaseNature(CompositeModule):
    """The Base Nature Module.
    Note:
        Look at [this tutorial](../tutorial/beginner/organize_model_structure.ipynb) to understand the model structure.
        This is NOT a raster layer, but can be seen as a container of different raster layers.
        Users can create new raster layer (i.e., `PatchModule`) by `new` method.
        By default, an initialized ABSESpy model will init an instance of this `BaseNature` as `nature` module.

    Attributes:
        major_layer:
            The major layer of nature module. By default, it's the first layer that user created.
        total_bounds:
            The spatial scope of the model's concern. By default, uses the major layer of this model.
    """

    def __init__(
        self, model: MainModel[Any, Any], name: str = "nature"
    ) -> None:
        CompositeModule.__init__(self, model, name=name)
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
        """委托给 major_layer 处理未找到的属性"""
        if name.startswith("_"):
            return super().__getattribute__(name)
        if self._major_layer is None:
            raise AttributeError(f"No major layer set and {name} not found")
        return getattr(self._major_layer, name)

    @property
    def major_layer(self) -> Optional[PatchModule]:
        """The major layer of nature module.
        By default, it's the first created layer.
        """
        return self._major_layer

    @major_layer.setter
    def major_layer(self, layer: PatchModule) -> None:
        if not isinstance(layer, PatchModule):
            raise TypeError(f"{layer} is not PatchModule.")
        self._major_layer = layer

    @property
    def total_bounds(self) -> np.ndarray:
        """Total bounds. The spatial scope of the model's concern.
        If None (by default), uses the major layer of this model.
        Usually, the major layer is the first layer sub-module you created.
        """
        if self.major_layer is None:
            raise ValueError(f"No major layer in {self.modules}.")
        return self.major_layer.total_bounds

    @property
    def crs(self) -> pyproj.CRS:
        """Geo CRS."""
        return (
            pyproj.CRS(CRS)
            if self.major_layer is None
            else self.major_layer.crs
        )

    def create_module(
        self,
        module_cls: Optional[Type[PatchModule]] = None,
        how: Optional[HowCreation] = None,
        major_layer: bool = False,
        **kwargs: Any,
    ) -> PatchModule:
        """Creates a submodule of the raster layer.

        Parameters:
            module_cls:
                The custom module class.
            how:
                Class method to call when creating the new sub-module (raster layer).
                So far, there are three options:
                    `from_resolution`: by selecting shape and resolution.
                    `from_file`: by input of a geo-tiff dataset.
                    `copy_layer`: by copying shape, resolution, bounds, crs, and coordinates of an existing submodule.
                if None (by default), just simply create a sub-module without any custom methods (i.e., use the base class `PatchModule`).
            **kwargs:
                Any other arg passed to the creation method.
                See corresponding method of your how option from `PatchModule` class methods.

        Returns:
            the created new module.
        """
        if self.modules.is_empty:
            major_layer = True
        module = self.modules.new(how=how, module_class=module_cls, **kwargs)
        # 如果是第一个创建的模块,则将其作为主要的图层
        if major_layer:
            self.major_layer = module
        setattr(self, module.name, module)
        return module
