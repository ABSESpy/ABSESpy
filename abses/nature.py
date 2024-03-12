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

import functools
from numbers import Number
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

import geopandas
import mesa_geo as mg
import numpy as np
import pyproj
import rasterio as rio
import rioxarray
import xarray as xr
from loguru import logger
from mesa.space import Coordinate
from mesa_geo.raster_layers import Cell
from rasterio import mask
from shapely import Geometry

from abses.modules import CompositeModule, Module
from abses.random import ListRandom

from .actor import Actor
from .cells import PatchCell
from .errors import ABSESpyError
from .sequences import ActorsList

if TYPE_CHECKING:
    from abses.main import MainModel

DEFAULT_WORLD = {
    "width": 10,
    "height": 10,
    "resolution": 1,
}
CRS = "epsg:4326"


class PatchModule(Module, mg.RasterLayer):
    """
    The spatial sub-module base class.
    Inherit from this class to create a submodule.
    [This tutorial](../tutorial/beginner/organize_model_structure.ipynb) shows the model structure.
    This is also a raster layer, inherited from the 'mesa-geo.RasterLayer' class.
    ABSESpy extends this class, so it can:
    1. place agents (by `_CellAgentsContainer` class.)
    2. work with `xarray`, `rasterio` packages for better data I/O workflow.

    Attributes:
        cell_properties:
            The accessible attributes of cells stored in this layer.
            When a `PatchCell`'s method is decorated by `raster_attribute`,
            it should be appeared here as a property attribute.
        attributes:
            All accessible attributes from this layer,
            including cell_properties.
        shape2d:
            Raster shape in 2D (heigh, width).
        shape3d:
            Raster shape in 3D (1, heigh, width),
            this is for compatibility with `mg.RasterLayer` and `rasterio`.
        array_cells:
            Array type of the `PatchCell` stored in this module.
        coords:
            Coordinate system of the raster data.
            This is useful when working with `xarray.DataArray`.
        random:
            A random proxy by calling the cells as an `ActorsList`.
    """

    def __init__(self, model, name=None, **kwargs):
        Module.__init__(self, model, name=name)
        mg.RasterLayer.__init__(self, **kwargs)
        logger.info("Initializing a new Model Layer...")
        logger.info(f"Using rioxarray version: {rioxarray.__version__}")

        for cell in self:
            cell.layer = self
        self._updated_ticks = []

    @property
    def cell_properties(self) -> set[str]:
        """The accessible attributes of cells stored in this layer.
        All `PatchCell` methods decorated by `raster_attribute` should be appeared here.
        """
        return self.cell_cls.__attribute_properties__()

    @property
    def attributes(self) -> set[str]:
        """All accessible attributes from this layer."""
        return self._attributes | self.cell_properties

    @property
    def shape2d(self) -> Coordinate:
        """Raster shape in 2D (height, width).
        This is useful when working with 2d `numpy.array`.
        """
        return self.height, self.width

    @property
    def shape3d(self) -> Coordinate:
        """Raster shape in 3D (1, heigh, width).
        This is useful when working with `rasterio` band.
        """
        return 1, self.height, self.width

    @property
    def array_cells(self) -> np.ndarray:
        """Array type of the `PatchCell` stored in this module."""
        return np.flipud(np.array(self.cells).T)

    @property
    def coords(self) -> Coordinate:
        """Coordinate system of the raster data.
        This is useful when working with `xarray.DataArray`.
        """
        x_arr = np.linspace(
            self.total_bounds[0], self.total_bounds[2], self.width
        )
        y_arr = np.linspace(
            self.total_bounds[3], self.total_bounds[1], self.height
        )
        return {
            "y": y_arr,
            "x": x_arr,
        }

    @classmethod
    def from_resolution(
        cls,
        model: MainModel,
        name: str = None,
        shape: Coordinate = (10, 10),
        crs: Optional[pyproj.CRS | str] = CRS,
        resolution: Number = 1,
        cell_cls: type[PatchCell] = PatchCell,
    ) -> Self:
        """Create a layer from resolution.

        Parameters:
            model:
                ABSESpy Model that the new module belongs.
            name:
                Name of the new module.
                If None (by default), using lowercase of the '__class__.__name__'.
                E.g., class Module -> module.
            shape:
                Array shape (height, width) of the new module.
                For example, `shape=(3, 5)` means the new module stores 15 cells.
            crs:
                Coordinate Reference Systems.
                If passing a string object, should be able to parsed by `pyproj`.
                By default, we use CRS = "epsg:4326".
            resolution:
                Spatial Resolution when creating the coordinates.
                By default 1, it means shape (3, 5) will generate coordinates:
                {y: [0, 1, 2], x: [0, 1, 2, 3, 4]}.
                Similar, when using resolution=0.1,
                it will be {y: [.0, .1, .2], x: [.0, .1, .2, .3, .4]}.
            cell_cls:
                Class type of `PatchCell` to create.

        Returns:
            A new instance of self ("PatchModule").
        """
        height, width = shape
        total_bounds = [0, 0, width * resolution, height * resolution]
        return cls(
            model,
            name=name,
            width=width,
            height=height,
            crs=crs,
            total_bounds=total_bounds,
            cell_cls=cell_cls,
        )

    @classmethod
    def copy_layer(
        cls,
        model: MainModel,
        layer: Self,
        name: Optional[str] = None,
        cell_cls: PatchCell = PatchCell,
    ) -> Self:
        """Copy an existing layer to create a new layer.

        Parameters:
            model:
                ABSESpy Model that the new module belongs.
            layer:
                Another layer to copy.
                These attributes will be copied:
                including the coordinates, the crs, and the shape.
            name:
                Name of the new module.
                If None (by default), using lowercase of the '__class__.__name__'.
                E.g., class Module -> module.
            cell_cls:
                Class type of `PatchCell` to create.

        Returns:
            A new instance of self ("PatchModule").
        """
        if not isinstance(layer, PatchModule):
            raise TypeError(f"{layer} is not a valid PatchModule.")

        return cls(
            model=model,
            name=name,
            width=layer.width,
            height=layer.height,
            crs=layer.crs,
            total_bounds=layer.total_bounds,
            cell_cls=cell_cls,
        )

    @classmethod
    def from_file(
        cls,
        raster_file: str,
        cell_cls: type[Cell] = PatchCell,
        attr_name: str | None = None,
        model: None | MainModel = None,
        name: str | None = None,
    ) -> Self:
        """Create a raster layer module from a file.

        Parameters:
            raster_file:
                File path of a geo-tiff dataset.
            model:
                ABSESpy Model that the new module belongs.
            attr_name:
                Assign a attribute name to the loaded raster data.
            name:
                Name of the new module.
                If None (by default), using lowercase of the '__class__.__name__'.
                E.g., class Module -> module.
            cell_cls:
                Class type of `PatchCell` to create.

        """
        with rio.open(raster_file, "r") as dataset:
            values = dataset.read()
            _, height, width = values.shape
            total_bounds = [
                dataset.bounds.left,
                dataset.bounds.bottom,
                dataset.bounds.right,
                dataset.bounds.top,
            ]
        obj = cls(
            model=model,
            name=name,
            width=width,
            height=height,
            crs=dataset.crs,
            total_bounds=total_bounds,
            cell_cls=cell_cls,
        )
        obj._transform = dataset.transform
        obj.apply_raster(values, attr_name=attr_name)
        return obj

    def _attr_or_array(self, data: None | str | np.ndarray) -> np.ndarray:
        """Determine the incoming data type and turn it into a reasonable array."""
        if data is None:
            return np.ones(self.shape2d)
        if isinstance(data, np.ndarray):
            if data.shape == self.shape2d:
                return data
            raise ABSESpyError(
                f"Shape mismatch: {data.shape} [input] != {self.shape2d} [expected]."
            )
        if isinstance(data, str) and data in self.attributes:
            return self.get_raster(data)
        raise TypeError("Invalid data type or shape.")

    def get_raster(self, attr_name: Optional[str] = None) -> np.ndarray:
        """Obtaining the Raster layer by attribute.

        Parameters:
            attr_name:
                The attribute to retrieve. Update it if it is a dynamic variable. If None (by default), retrieve all attributes as a 3D array.

        Returns:
            A 3D array of attribute.
        """
        if attr_name not in self._dynamic_variables:
            return super().get_raster(attr_name)
        return self.dynamic_var(attr_name=attr_name).reshape(self.shape3d)

    def dynamic_var(self, attr_name: str) -> np.ndarray:
        """Update and get dynamic variable.

        Parameters:
            attr_name:
                The dynamic variable to retrieve.

        Returns:
            2D numpy.ndarray data of the variable.
        """
        if self.time.tick in self._updated_ticks:
            return super().dynamic_var(attr_name)
        array = super().dynamic_var(attr_name)
        # 判断算出来的是一个符合形状的矩阵
        self._attr_or_array(array)
        # 将矩阵转换为三维，并更新空间数据
        array_3d = array.reshape(self.shape3d)
        self.apply_raster(array_3d, attr_name=attr_name)
        self._updated_ticks.append(self.time.tick)
        return array

    def get_rasterio(self, attr_name: str | None = None) -> rio.MemoryFile:
        """Gets the Rasterio raster layer corresponding to the attribute. Save to a temporary rasterio memory file.

        Parameters:
            attr_name:
                The attribute name for creating the rasterio file.

        Returns:
            The rasterio tmp memory file of raster.
        """
        if attr_name is None:
            data = np.ones(self.shape2d)
        else:
            data = self.get_raster(attr_name=attr_name)
        # 如果获取到的是2维，重整为3维
        if len(data.shape) != 3:
            data = data.reshape(self.shape3d)
        with rio.MemoryFile() as mem_file:
            with mem_file.open(
                driver="GTiff",
                height=data.shape[1],
                width=data.shape[2],
                count=data.shape[0],  # number of bands
                dtype=str(data.dtype),
                crs=self.crs,
                transform=self.transform,
            ) as dataset:
                dataset.write(data)
            # Open the dataset again for reading and return
            return mem_file.open()

    def get_xarray(self, attr_name: Optional[str] = None) -> xr.DataArray:
        """Get the xarray raster layer with spatial coordinates.

        Parameters:
            attr_name:
                The attribute to retrieve. If None (by default), return all available attributes (3D DataArray). Otherwise, 2D DataArray of the chosen attribute.

        Returns:
            Xarray.DataArray data with spatial coordinates of the chosen attribute.
        """
        data = self.get_raster(attr_name=attr_name)
        if attr_name:
            name = attr_name
            data = data.reshape(self.shape2d)
            coords = self.coords
        else:
            coords = {"variable": list(self.attributes)}
            coords |= self.coords
            name = self.name
        return xr.DataArray(
            data=data,
            name=name,
            coords=coords,
        ).rio.write_crs(self.crs)

    @property
    def random(self) -> ListRandom:
        """Randomly"""
        return self.select().random

    def _select_by_geometry(
        self, geometry: Geometry, refer_layer: Optional[str] = None, **kwargs
    ) -> np.ndarray:
        """Gets all the cells that intersect the given geometry.

        Parameters:
            geometry:
                Shapely Geometry to search intersected cells.
            refer_layer:
                The attribute name to refer when filtering cells.
            **kwargs:
                Args pass to the function `rasterio.mask.mask`. It influence how to build the mask for filtering cells. Please refer [this doc](https://rasterio.readthedocs.io/en/latest/api/rasterio.mask.html) for details.

        Raises:
            ABSESpyError:
                If no available attribute exists, or the assigned refer layer is not available in the attributes.

        Returns:
            A list of PatchCell.
        """
        if refer_layer is not None and refer_layer not in self.attributes:
            raise ABSESpyError(
                f"The refer layer {refer_layer} is not available in the attributes"
            )
        data = self.get_rasterio(attr_name=refer_layer)
        out_image, _ = mask.mask(data, [geometry], **kwargs)
        return out_image.reshape(self.shape2d)

    def select(
        self, where: Optional[str | np.ndarray | Geometry] = None
    ) -> ActorsList[PatchCell]:
        """Select cells from this layer.

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
        if isinstance(where, Geometry):
            mask_ = self._select_by_geometry(geometry=where)
        elif (
            isinstance(where, (np.ndarray, str, xr.DataArray)) or where is None
        ):
            mask_ = self._attr_or_array(where).reshape(self.shape2d)
        else:
            raise TypeError(
                f"{type(where)} is not supported for selecting cells."
            )
        return ActorsList(self.model, self.array_cells[mask_.astype(bool)])

    def apply(self, ufunc: Callable, *args: Any, **kwargs: Any) -> np.ndarray:
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
        func = functools.partial(ufunc, *args, **kwargs)
        return np.vectorize(func)(self.array_cells, *args, **kwargs)


class BaseNature(mg.GeoSpace, CompositeModule):
    """The Base Nature Module.
    Note:
        Look at [this tutorial](../tutorial/beginner/organize_model_structure.ipynb) to understand the model structure.
        This is NOT a raster layer, but can be seen as a container of different raster layers.
        Users can create new raster layer (i.e., `PatchModule`) by `create_module` method.
        By default, an initialized ABSESpy model will init an instance of this `BaseNature` as `nature` module.

    Attributes:
        major_layer:
            The major layer of nature module. By default, it's the first layer that user created.
        total_bounds:
            The spatial scope of the model's concern. By default, uses the major layer of this model.
    """

    def __init__(self, model, name="nature"):
        CompositeModule.__init__(self, model, name=name)
        crs = self.params.get("crs", CRS)
        mg.GeoSpace.__init__(self, crs=crs)
        self._major_layer = None

        logger.info("Initializing a new Base Nature module...")

    @property
    def major_layer(self) -> PatchModule | None:
        """The major layer of nature module.
        By default, it's the first created layer.
        """
        return self._major_layer

    @major_layer.setter
    def major_layer(self, layer: PatchModule):
        if not isinstance(layer, PatchModule):
            raise TypeError(f"{layer} is not PatchModule.")
        self._major_layer = layer
        self.crs = layer.crs

    @property
    def total_bounds(self) -> np.ndarray | None:
        """Total bounds. The spatial scope of the model's concern.
        If None (by default), uses the major layer of this model.
        Usually, the major layer is the first layer sub-module you created.
        """
        if self._total_bounds is not None:
            return self._total_bounds
        if hasattr(self, "major_layer") and self.major_layer:
            return self.major_layer.total_bounds
        return None

    def create_agents_from_gdf(
        self,
        gdf: geopandas.GeoDataFrame,
        unique_id: str = "Index",
        agent_cls: type[Actor] = Actor,
    ) -> ActorsList[Actor]:
        """Create actors from a `geopandas.GeoDataFrame` object.

        Parameters:
            gdf:
                The `geopandas.GeoDataFrame` object to convert.
            unique_id:
                A column name, to be converted to unique index
                of created geo-agents (Social-ecological system Actors).
            agent_cls:
                Agent class to create.

        Returns:
            An `ActorsList` with all new created actors stored.
        """
        creator = mg.AgentCreator(
            model=self.model, agent_class=agent_cls, crs=self.crs
        )
        agents = creator.from_GeoDataFrame(gdf=gdf, unique_id=unique_id)
        self.model.agents.register(agent_cls)
        self.model.agents.add(agents)
        return ActorsList(model=self.model, objs=agents)

    def create_module(
        self,
        module_class: Module = PatchModule,
        how: str | None = None,
        **kwargs: Dict[str, Any],
    ) -> PatchModule:
        """Creates a submodule of the raster layer.

        Parameters:
            module_class:
                The custom module class.
            how:
                Class method to call when creating the new sub-module (raster layer). So far, there are three options:
                    `from_resolution`: by selecting shape and resolution.
                    `from_file`: by input of a geo-tiff dataset.
                    `copy_layer`: by copying shape, resolution, bounds, crs, and coordinates of an existing submodule.
                if None (by default), just simply create a sub-module without any custom methods (i.e., use the base class `PatchModule`).
            **kwargs:
                Any other arg passed to the creation method. See corresponding method of your how option from `PatchModule` class methods.

        Returns:
            the created new module.
        """
        module = super().create_module(module_class, how, **kwargs)
        # 如果是第一个创建的模块,则将其作为主要的图层
        if not self.layers:
            self.major_layer = module
        self.add_layer(module)
        return module
