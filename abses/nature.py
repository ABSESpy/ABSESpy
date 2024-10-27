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

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterator,
    Optional,
    Protocol,
    Type,
    overload,
)

import numpy as np
import pyproj
import rasterio
import xarray as xr
from mesa.space import Coordinate

from abses._bases.modules import CompositeModule, HowCreation
from abses.cells import PatchCell
from abses.patch import (
    CRS,
    CellFilter,
    PatchModule,
    Raster,
    _PatchModuleFactory,
)
from abses.random import ListRandom
from abses.sequences import ActorsList
from abses.viz.viz_nature import _VizNature

if TYPE_CHECKING:
    from abses.main import MainModel


class _PatchModuleProtocol(Protocol):
    @property
    def cells(self) -> ActorsList[PatchCell]:
        """The cells stored in this layer."""

    @property
    def mask(self) -> np.ndarray:
        """Where is not accessible."""

    @property
    def cell_properties(self) -> set[str]:
        """The accessible attributes of cells stored in this layer.
        All `PatchCell` methods decorated by `raster_attribute` should be appeared here.
        """

    @property
    def xda(self) -> xr.DataArray:
        """Get the xarray raster layer with spatial coordinates."""

    @property
    def plot(self) -> _VizNature:
        """Plotting"""

    @property
    def attributes(self) -> set[str]:
        """All accessible attributes from this layer."""

    @property
    def shape2d(self) -> Coordinate:
        """Raster shape in 2D (height, width).
        This is useful when working with 2d `numpy.array`.
        """

    @property
    def shape3d(self) -> Coordinate:
        """Raster shape in 3D (1, heigh, width).
        This is useful when working with `rasterio` band.
        """

    @property
    def array_cells(self) -> np.ndarray:
        """Array type of the `PatchCell` stored in this module."""

    @property
    def coords(self) -> Coordinate:
        """Coordinate system of the raster data.
        This is useful when working with `xarray.DataArray`.
        """

    def to_crs(self, crs, inplace=False) -> Optional[PatchModule]:
        """Converting the raster data to a another CRS."""

    def dynamic_var(self, attr_name: str) -> np.ndarray:
        """Update and get dynamic variable.

        Parameters:
            attr_name:
                The dynamic variable to retrieve.

        Returns:
            2D numpy.ndarray data of the variable.
        """

    def get_xarray(self, attr_name: Optional[str] = None) -> xr.DataArray:
        """Get the xarray raster layer with spatial coordinates.

        Parameters:
            attr_name:
                The attribute to retrieve. If None (by default),
                return all available attributes (3D DataArray).
                Otherwise, 2D DataArray of the chosen attribute.

        Returns:
            Xarray.DataArray data with spatial coordinates of the chosen attribute.
        """

    def out_of_bounds(self, pos: Coordinate) -> bool:
        """Check if a pos is out of the bounds.
        This is a protocol method.
        """

    @property
    def random(self) -> ListRandom:
        """Randomly"""

    def select(
        self,
        where: Optional[CellFilter] = None,
    ) -> ActorsList[PatchCell]:
        """Select cells from this layer.
        Also has a shortcut alias for this method: `.sel`.

        Parameters:
            where:
                The condition to select cells.
                If None (by default), select all cells.
                If a string, select cells by the attribute name.
                If a numpy.ndarray, select cells by the mask array.
                If a Shapely Geometry, select cells by the intersection with the geometry.

        Raises:
            TypeError:
                If the input type is not supported.

        Returns:
            An `ActorsList` with all selected cells stored.
        """

    def apply(
        self, ufunc: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> np.ndarray:
        """Apply a function to array cells.

        Parameters:
            ufunc:
                A function to apply.
            *args:
                Positional arguments to pass to the function.
            **kwargs:
                Keyword arguments to pass to the function.

        Returns:
            The result of the function applied to the array cells.
        """

    def coord_iter(self) -> Iterator[tuple[Coordinate, PatchCell]]:
        """
        An iterator that returns coordinates as well as cell contents.
        """

    def apply_raster(
        self, data: Raster, attr_name: Optional[str], **kwargs: Any
    ) -> None:
        """Apply raster data to the cells.

        Parameters:
            data:
                np.ndarray data: 2D numpy array with shape (1, height, width).
                xr.DataArray data: xarray DataArray with spatial coordinates.
                xr.Dataset data: xarray Dataset with spatial coordinates.
            attr_name:
                Name of the attribute to be added to the cells.
                If None, a random name will be generated.
                Default is None.
            **kwargs:
                cover_crs:
                    Whether to cover the crs of the input data.
                    If False, it assumes the input data has crs info.
                    If True, it will cover the crs of the input data by the crs of this layer.
                    Default is False.
                resampling_method:
                    The [resampling method](https://rasterio.readthedocs.io/en/stable/api/rasterio.enums.html#rasterio.enums.Resampling)
                    when re-projecting the input data.
                    Default is "nearest".
                flipud:
                    Whether to flip the input data upside down.
                    Set to True when the input data is not in the same direction as the raster layer.
                    Default is False.
        """

    def to_file(
        self,
        raster_file: str,
        attr_name: Optional[str] = None,
        driver: str = "GTiff",
    ) -> None:
        """
        Writes a raster layer to a file.

        Parameters:
            raster_file:
                The path to the raster file to write to.
            attr_name:
                The name of the attribute to write to the raster.
                If None, all attributes are written. Default is None.
            driver:
                The GDAL driver to use for writing the raster file.
                Default is 'GTiff'.
                See GDAL docs at https://gdal.org/drivers/raster/index.html.
        """

    def get_raster(self, attr_name: Optional[str] = None) -> np.ndarray:
        """Obtaining the Raster layer by attribute.

        Parameters:
            attr_name:
                The attribute to retrieve.
                If None (by default), retrieve all attributes as a 3D array.

        Returns:
            A 3D array of attribute.
        """

    @overload
    def get_neighborhood(
        self,
        pos: Coordinate,
        moore: bool,
        include_center: bool = False,
        radius: int = 1,
        annular: bool = False,
        return_mask: bool = True,
    ) -> np.ndarray:
        ...

    def get_neighborhood(
        self,
        pos: Coordinate,
        moore: bool,
        include_center: bool = False,
        radius: int = 1,
        annular: bool = False,
        return_mask: bool = False,
    ) -> ActorsList[PatchCell] | np.ndarray:
        """Get neighbors of the given position.
        This is a protocol method.
        """


class BaseNature(CompositeModule, _PatchModuleProtocol):
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

    def __getattribute__(self, name: str) -> PatchModule:
        """Get the submodule by name."""
        if name.startswith("_"):
            return super().__getattribute__(name)
        if hasattr(_PatchModuleProtocol, name):
            return getattr(self.major_layer, name)
        return super().__getattribute__(name)

    def __getattr__(self, name: str) -> PatchModule:
        if name in self._modules:
            return self._modules[name]
        raise AttributeError(f"Unknown module {name}")

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
