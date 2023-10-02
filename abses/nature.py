#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, List, Optional, Self

import geopandas
import mesa_geo as mg
import numpy as np
import rasterio as rio
import rioxarray
import xarray as xr
from mesa.space import Coordinate
from mesa_geo.raster_layers import Cell
from rasterio import mask

from abses.modules import CompositeModule, Module

from .actor import Actor
from .cells import PatchCell
from .sequences import ActorsList
from .tools.func import norm_choice

if TYPE_CHECKING:
    from abses.main import MainModel

logger = logging.getLogger(__name__)
logger.info("Using rioxarray version: %s", rioxarray.__version__)

DEFAULT_WORLD = {
    "width": 10,
    "height": 10,
    "resolution": 1,
}
CRS = "epsg:4326"


class PatchModule(Module, mg.RasterLayer):
    """基础的空间模块"""

    def __init__(self, model, name=None, **kwargs):
        Module.__init__(self, model, name=name)
        mg.RasterLayer.__init__(self, **kwargs)
        for cell in self.array_cells.flatten():
            cell.layer = self
        self._file = None

    @property
    def cell_properties(self) -> set[str]:
        """属性"""
        return self.cell_cls.__attribute_properties__()

    @property
    def attributes(self) -> set[str]:
        """属性"""
        return self._attributes | self.cell_properties

    @property
    def file(self) -> str | None:
        """文件路径"""
        return self._file

    @property
    def shape2d(self) -> Coordinate:
        """形状"""
        return self.height, self.width

    @property
    def shape3d(self) -> Coordinate:
        """形状"""
        return 1, self.height, self.width

    @property
    def array_cells(self) -> np.ndarray:
        """所有格子的二维数组形式"""
        return np.flipud(np.array(self.cells).T)

    @property
    def coords(self) -> Coordinate:
        """维度"""
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
        model,
        name=None,
        shape: Coordinate = (10, 10),
        crs=None,
        resolution=1,
        cell_cls: type[PatchCell] = PatchCell,
    ) -> Self:
        """从分辨率创建栅格图层"""
        height, width = shape
        total_bounds = [0, 0, width * resolution, height * resolution]
        if crs is None:
            crs = CRS
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
        """复制一个已有图层的属性来创建新图层"""
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
        """从文件创建栅格图层"""
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
        """判断传入的数据类型，变成合理的数组"""
        if data is None:
            return np.ones(self.shape2d)
        if isinstance(data, np.ndarray):
            if data.shape == self.shape2d:
                return data
            else:
                raise ValueError(
                    f"Shape mismatch: {data.shape} [input] != {self.shape2d} [expected]."
                )
        if isinstance(data, str) and data in self.attributes:
            return self.get_raster(data)
        raise TypeError("Invalid data type or shape.")

    def get_raster(self, attr_name: str | None = None) -> np.ndarray:
        """
        获取属性对应的 Raster 栅格图层之前，如果是动态变量就先更新
        """
        if attr_name not in self._dynamic_variables:
            return super().get_raster(attr_name)
        return self.dynamic_var(attr_name=attr_name).reshape(self.shape3d)

    def dynamic_var(self, attr_name: str) -> Any:
        """获取动态变量"""
        array = super().dynamic_var(attr_name)
        # 判断算出来的是一个符合形状的矩阵
        self._attr_or_array(array)
        # 将矩阵转换为三维，并更新空间数据
        array_3d = array.reshape(self.shape3d)
        self.apply_raster(array_3d, attr_name=attr_name)
        return array

    def get_rasterio(self, attr_name: str | None = None) -> rio.MemoryFile:
        """获取属性对应的 Rasterio 栅格图层"""
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

    def geometric_cells(self, geometry, **kwargs) -> List[PatchCell]:
        """获取所有与给定几何形状相交的格子"""
        data = self.get_rasterio(list(self.attributes)[0])
        out_image, _ = mask.mask(data, [geometry], **kwargs)
        mask_ = out_image.reshape(self.shape2d)
        return list(self.array_cells[mask_.astype(bool)])

    def link_by_geometry(
        self, geo_agent: Actor, link: Optional[str] = None, **kwargs
    ) -> None:
        """将所有与给定几何形状相交的格子关联"""
        if not hasattr(geo_agent, "geometry"):
            raise TypeError(f"Agent {geo_agent} has no geometry.")
        cells = self.geometric_cells(geo_agent.geometry, **kwargs)
        for cell in cells:
            cell.link_to(agent=geo_agent, link=link)

    def batch_link_by_geometry(
        self, geo_agents: List[Actor], link: Optional[str] = None, **kwargs
    ) -> None:
        """批量将根据几何形状将相交的格子分配给主体"""
        for geo_agent in geo_agents:
            self.link_by_geometry(geo_agent, link, **kwargs)

    def linked_attr(
        self,
        attr: str,
        link: Optional[str] = None,
        nodata: Any = np.nan,
        how: Optional[str] = "only",
    ) -> np.ndarray:
        """获取链接到本图层的主体属性"""

        def get_attr(cell: PatchCell, __name):
            return cell.linked_attr(
                attr=__name,
                link=link,
                nodata=nodata,
                how=how,
            )

        return np.vectorize(get_attr)(self.array_cells, attr)

    def get_xarray(self, attr_name: str | None = None) -> xr.DataArray:
        """获取 xarray 栅格图层，并设置空间投影"""
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
        Choose 'k' PatchCell in the layer randomly.

        Args:
            k (int): number of patches to choose.
            mask (np.ndarray, optional): bool mask, only True patches can be choose. If None, all patches are accessible. Defaults to None.
            replace (bool, optional): If a patch can be chosen more than once. Defaults to False.

        Returns:
            List[Coordinate]: iterable coordinates of chosen patches.
        """
        where = self._attr_or_array(where).flatten()
        prob = self._attr_or_array(prob).flatten()
        masked_prob = np.where(where, np.nan, prob)
        return norm_choice(
            self.array_cells.flatten(),
            size=k,
            p=masked_prob,
            replace=replace,
        )

    def has_agent(
        self, link: Optional[str] = None, xarray: bool = False
    ) -> np.ndarray:
        """有多少个绑定的主体"""
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
        将土地分配给主体
        """
        mask_ = self._attr_or_array(where)
        cells = self.array_cells[mask_]
        for cell in cells:
            cell.link_to(agent, link)

    def move_agent(self, agent: Actor, position: Coordinate) -> None:
        """移动主体"""
        if agent.layer is not self:
            raise TypeError(f"Agent {agent} is not on {self}.")
        agent.put_on_layer(self, position)


class BaseNature(mg.GeoSpace, CompositeModule):
    """最主要的自然模块"""

    def __init__(self, model, name="nature"):
        CompositeModule.__init__(self, model, name=name)
        crs = self.params.get("crs", CRS)
        mg.GeoSpace.__init__(self, crs=crs)
        self._major_layer = None

    @property
    def major_layer(self) -> PatchModule | None:
        """作为参考的最主要的图层"""
        return self._major_layer

    @major_layer.setter
    def major_layer(self, layer: PatchModule):
        if not isinstance(layer, PatchModule):
            raise TypeError(f"{layer} is not PatchModule.")
        self._major_layer = layer
        self.crs = layer.crs

    @property
    def total_bounds(self) -> np.ndarray | None:
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
    ) -> ActorsList:
        """根据GeoDataFrame创建主体"""
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
        """创建栅格图层的子模块"""
        module = super().create_module(module_class, how, **kwargs)
        # 如果是第一个创建的模块,则将其作为主要的图层
        if not self.layers:
            self.major_layer = module
        self.add_layer(module)
        return module
