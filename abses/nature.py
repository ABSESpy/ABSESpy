#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from numbers import Number
from typing import TYPE_CHECKING, Any, Iterable, List, Optional, Self

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

from abses.links import LinkNode
from abses.modules import CompositeModule, Module

from .actor import Actor
from .cells import PatchCell
from .errors import ABSESpyError
from .sequences import ActorsList

if TYPE_CHECKING:
    from abses.main import MainModel

# logger = logging.getLogger(__name__)
# logger.info("Using rioxarray version: %s", rioxarray.__version__)

DEFAULT_WORLD = {
    "width": 10,
    "height": 10,
    "resolution": 1,
}
CRS = "epsg:4326"


class PatchModule(Module, mg.RasterLayer):
    # 基础的空间模块，继承这个类来创建一个子模块。看[这个教程](../features/architectural_elegance.md)来了解模型结构。这也是一个栅格图层，继承自 `mesa-geo` 的`RasterLayer`类，并可以放置主体。
    """
    The spatial sub-module base class.
    Inherit from this class to create a submodule. Look at [this tutorial](../features/architectural_elegance.md) to understand the model structure. This is also a raster layer, inherited from the 'mesa-geo.RasterLayer' class, and can place agents.

    Attributes:
        cell_properties:
            The accessible attributes of cells stored in this layer. All `PatchCell` methods which are decorated by the decorator `raster_attribute` should be appeared here.
        attributes:
            All accessible attributes from this layer.
        file:
            If the module is created by reading a raster dataset, save the file path.
        shape2d:
            Raster shape in 2D (heigh, width).
        shape3d:
            Raster shape in 3D (1, heigh, width).
    """

    def __init__(self, model, name=None, **kwargs):
        Module.__init__(self, model, name=name)
        mg.RasterLayer.__init__(self, **kwargs)
        logger.info("Initializing a new Model Layer...")
        logger.info(f"Using rioxarray version: {rioxarray.__version__}")

        for cell in self.array_cells.flatten():
            cell.layer = self
        self._file = None

    @property
    def cell_properties(self) -> set[str]:
        """The accessible attributes of cells stored in this layer. All `PatchCell` methods which are decorated by the decorator `raster_attribute` should be appeared here."""
        return self.cell_cls.__attribute_properties__()

    @property
    def attributes(self) -> set[str]:
        """All accessible attributes from this layer."""
        return self._attributes | self.cell_properties

    @property
    def file(self) -> str | None:
        """If the module is created by reading a raster dataset, save the file path."""
        return self._file

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
                Name of the new module. If None (by default), using lowercase of the '__class__.__name__'. E.g., class NewModule -> newmodule.
            shape:
                Array shape (height, width) of the new module. For example, if shape=(3, 5), it means the new module will store 15 cells.
            crs:
                Coordinate Reference Systems. If passing a string object, should be able to parsed by `pyproj`. By default, we use CRS = "epsg:4326".
            resolution:
                Spatial Resolution when creating the coordinates. By default 1, it means shape (3, 5) will generate coordinates like {y: [0, 1, 2], x: [0, 1, 2, 3, 4]}. Similar, when using resolution=0.1, it will be {y: [.0, .1, .2], x: [.0, .1, .2, .3, .4]}.
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
                Another layer to copy. These attributes will be copied: the coordinates, the crs, and the shape.
            name:
                Name of the new module. If None (by default), using lowercase of the '__class__.__name__'. E.g., class NewModule -> newmodule.
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
                Name of the new module. If None (by default), using lowercase of the '__class__.__name__'. E.g., class NewModule -> newmodule.
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
        obj._file = raster_file
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

    def get_raster(self, attr_name: str | None = None) -> np.ndarray:
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
        array = super().dynamic_var(attr_name)
        # 判断算出来的是一个符合形状的矩阵
        self._attr_or_array(array)
        # 将矩阵转换为三维，并更新空间数据
        array_3d = array.reshape(self.shape3d)
        self.apply_raster(array_3d, attr_name=attr_name)
        return array

    def get_rasterio(self, attr_name: str | None = None) -> rio.MemoryFile:
        """Gets the Rasterio raster layer corresponding to the attribute. Save to a temporary rasterio memory file.

        Parameters:
            attr_name:
                The attribute name for creating the rasterio file.

        Returns:
            The rasterio tmp memory file of raster.
        """
        data = self.get_raster(attr_name=attr_name)
        # 如果获取到的是2维，重整为3维
        if len(data.shape):
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

    def geometric_cells(
        self, geometry: Geometry, refer_layer: str | None = None, **kwargs
    ) -> List[PatchCell]:
        """Gets all the cells that intersect the given geometry.

        Parameters:
            geometry:
                Shapely Geometry to search intersected cells.
            **kwargs:
                Args pass to the function `rasterio.mask.mask`. It influence how to build the mask for filtering cells. Please refer [this doc](https://rasterio.readthedocs.io/en/latest/api/rasterio.mask.html) for details.

        Raises:
            ABSESpyError:
                If no available attribute exists, or the assigned refer layer is not available in the attributes.

        Returns:
            A list of PatchCell.
        """
        if not self.attributes:
            raise ABSESpyError(
                "No available attribute, at least one as refer."
            )
        if refer_layer is None:
            refer_layer = list(self.attributes)[0]
        if refer_layer not in self.attributes:
            raise ABSESpyError(
                f"The refer layer {refer_layer} is not available in the attributes"
            )
        data = self.get_rasterio(attr_name=refer_layer)
        out_image, _ = mask.mask(data, [geometry], **kwargs)
        mask_ = out_image.reshape(self.shape2d)
        return list(self.array_cells[mask_.astype(bool)])

    def link_by_geometry(
        self,
        actors: Actor | Iterable[Actor],
        link: Optional[str] = None,
        refer_layer: str | None = None,
        **kwargs,
    ) -> None:
        """Relates all cells intersecting a given geometry.

        Parameters:
            geo_agent:
                An Actor or an iterable object of actors (e.g., `ActorsList`) who has existing geometry.
                This method allows each agent create a mask by the geometry, and then link the cells within the sphere to this agent.
            link:
                The link info to save.
            refer_layer:
                The layer to be a refer of spatial sphere.
                If the referred layer has nodata in some cells,
                those cells won't be linked to his actor.
            **kwargs:
                Args pass to the function `rasterio.mask.mask`. It influence how to build the mask for filtering cells. Please refer [this doc](https://rasterio.readthedocs.io/en/latest/api/rasterio.mask.html) for details.

        Raises:
            TypeError:
                If the input agent type is not inherit from `Actor`.
            AttributeError:
                The current actor doesn't have a valid geometry info.
            ABSESpyError:
                If the referred layer is not available in attributes.
        """
        if hasattr(actors, "__iter__"):
            for agent in actors:
                self.link_by_geometry(agent, link, refer_layer, **kwargs)
            return
        # For a single actor
        if not isinstance(actors, LinkNode):
            raise TypeError(
                f"Type '{type(actors)}' can not be linked, make sure your agent is a valid subclass of `Actor`."
            )
        if not actors.geometry:
            raise AttributeError(f"Agent {actors} has no geometry.")
        cells = self.geometric_cells(
            actors.geometry, refer_layer=refer_layer, **kwargs
        )
        for cell in cells:
            cell.link_to(agent=actors, link=link)

    def linked_attr(
        self,
        attr_name: str,
        link: Optional[str] = None,
        nodata: Any = np.nan,
        how: Optional[str] = "only",
    ) -> np.ndarray:
        """Gets the attribute linked to this layer.

        Parameters:
            attr_name:
                The attribute name to search.
            link:
                The link name to get. If None (by default), get the actors located at each cell.
            nodata:
                On the cells without linked agent or located agent, return this nodata.
            how:
                Search mode. Choose the behave when a cell is linked to or have more than one agent.
                    If 'only', raises ABSESpyError when more than one agent is found.
                    If 'random', random choose an agent from all searched agents.

        Returns:
            An array of searched attribute.
        """

        def get_attr(cell: PatchCell, __name):
            return cell.linked_attr(
                attr=__name,
                link=link,
                nodata=nodata,
                how=how,
            )

        return np.vectorize(get_attr)(self.array_cells, attr_name)

    def get_xarray(self, attr_name: str | None = None) -> xr.DataArray:
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

    def random_positions(
        self,
        k: int = 1,
        where: str | np.ndarray = None,
        prob: str | np.ndarray = None,
        replace: bool = False,
    ) -> List[Coordinate]:
        """
        Choose 'k' `PatchCell` in the layer randomly.

        Parameters:
            k:
                number of patches to choose.
            mask:
                bool mask, only True patches can be choose. If None, all patches are accessible. Defaults to None.
            prob:
                probability of each available position.
            replace:
                If a patch can be chosen more than once. Defaults to False.

        Returns:
            Iterable coordinates of chosen patches.
        """
        where = self._attr_or_array(where).flatten()
        prob = self._attr_or_array(prob).flatten()
        masked_prob = np.where(where, np.nan, prob)
        all_cells = ActorsList(self.model, self.array_cells.flatten())
        return all_cells.random.choice(
            size=k, prob=masked_prob, replace=replace
        )

    def has_agent(
        self, link: Optional[str] = None, xarray: bool = False
    ) -> np.ndarray:
        """If any actor is linked or existed in each cell.

        Parameters:
            link:
                Link to search. If None (by default), search if any actor is located at in each cell.
            xarray:
                If True, return `Xarray.DataArray` object, `np.ndarray` otherwise (by default).

        Returns:
            A raster data shows weather any actor links or exists.
        """
        if link is None:
            data = np.vectorize(lambda x: x.has_agent)(self.array_cells)
        else:
            data = np.vectorize(lambda x: bool(x.linked(link)))(
                self.array_cells
            )
        if xarray:
            return xr.DataArray(
                data=data,
                coords=self.coords,
                name=link or "has_agent",
            ).rio.write_crs(self.crs)
        return data

    def land_allotment(
        self, agent: Actor, link: str, where: None | str | np.ndarray = None
    ) -> None:
        """
        Allotment of land of this layer to actors.

        Parameters:
            agent:
                the actor to Affirmation of land link.
            link:
                link name of the association.
            where:
                if None, all cells will be selected.
                if str, choose the corresponding attribute raster array as the mask.
                if ndarray, the input array should has the same 2d-shape with this layer.

        Raises:
            ABSESpyError:
                If the shape of input array is not aligned with the shape of this layer.
        """
        mask_ = self._attr_or_array(where)
        cells = self.array_cells[mask_]
        for cell in cells:
            cell.link_to(agent, link)


class BaseNature(mg.GeoSpace, CompositeModule):
    """The Base Nature Module.
    Note:
        Look at [this tutorial](../features/architectural_elegance.md) to understand the model structure.
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
        By default, it's the first layer that user created.
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
        if self._total_bounds:
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
                A column name, denotes which column will be converted to unique index of created geo-agents (Social-ecological system Actors).
            agent_cls:
                Agent class to create.

        Returns:
            An `ActorsList` with all new created actors stored.
        """
        creator = mg.AgentCreator(
            model=self.model, agent_class=agent_cls, crs=self.crs
        )
        agents = creator.from_GeoDataFrame(gdf=gdf, unique_id=unique_id)
        self.model.agents.register_a_breed(agent_cls)
        self.model.agents.add(agents)
        return ActorsList(model=self.model, objs=agents)

    def create_module(
        self,
        module_class: Module = PatchModule,
        how: str | None = None,
        **kwargs,
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
