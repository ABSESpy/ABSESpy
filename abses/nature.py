#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional, Self

import mesa_geo as mg
import numpy as np
import rasterio as rio
from mesa.space import Coordinate
from mesa_geo.raster_layers import Cell, RasterLayer
from rasterio import mask

from .modules import CompositeModule, Module
from .sequences import ActorsList
from .tools.func import norm_choice

if TYPE_CHECKING:
    from abses.actor import Actor
    from abses.main import MainModel

DEFAULT_WORLD = {
    "width": 10,
    "height": 10,
    "resolution": 1,
}
CRS = "epsg:4326"


class PatchCell(mg.Cell):
    """斑块"""

    def __init__(self, pos=None, indices=None):
        super().__init__(pos, indices)
        self._attached_agents = {}
        self._agents = set()

    def __repr__(self) -> str:
        return f"<PatchCell at {self.pos}>"

    @property
    def links(self) -> List[str]:
        """所有关联类型"""
        return list(self._attached_agents.keys())

    @property
    def agents(self) -> ActorsList:
        """该斑块上的所有主体"""
        return ActorsList(self.model, self._agents)

    def add(self, agent) -> None:
        """将一个主体添加到该处"""
        self._agents.add(agent)

    def remove(self, agent) -> None:
        """将一个此处的主体移除"""
        self._agents.remove(agent)

    def link_to(
        self, agent: Actor, link: Optional[str] = None, update: bool = False
    ) -> None:
        """
        将一个主体与该地块关联，一个地块只能关联到一个主体。
        如果一个地块属于多个主体的情况，需要为多个主体建立一个虚拟主体。
        即，我们假设产权是明晰的。
        """
        if link is None:
            link = f"Link_{len(self._attached_agents)}"
        if link in self.links and not update:
            raise KeyError(
                f"{link} already exists, set update to True for updating."
            )
        self._attached_agents[link] = agent

    def detach(self, label: str) -> None:
        """取消某个主体与该斑块的联系"""
        if label not in self.links:
            raise KeyError(f"{label} is not a registered link.")
        del self._attached_agents[label]

    def linked(
        self, link: str, nodata: Optional[Any] = None, restrict: bool = False
    ) -> Actor:
        """获取链接到该斑块的主体"""
        if restrict and link not in self.links:
            raise KeyError(f"Link {link} not exists in {self.links}.")
        return self._attached_agents.get(link, nodata)


class PatchModule(Module, mg.RasterLayer):
    """基础的空间模块"""

    def __init__(self, model, name=None, **kwargs):
        Module.__init__(self, model, name=name)
        mg.RasterLayer.__init__(self, **kwargs)
        self._file = None

    @property
    def file(self) -> str | None:
        """文件路径"""
        return self._file

    @property
    def shape(self) -> Coordinate:
        """形状"""
        return self.width, self.height

    @property
    def array_cells(self) -> np.ndarray:
        """所有格子的二维数组形式"""
        return np.array(self.cells)

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
        width, height = shape
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
    def from_file(
        cls,
        raster_file: str,
        cell_cls: type[Cell] = PatchCell,
        attr_name: str | None = None,
        model: None | MainModel = None,
        name: str | None = None,
    ) -> RasterLayer:
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
        if data is None:
            return np.ones(self.shape)
        if isinstance(data, np.ndarray) and data.shape == self.shape:
            return data
        if isinstance(data, str) and data in self.attributes:
            return self.get_raster(data)
        raise TypeError("Invalid data type or shape.")

    def get_rasterio(self, attr_name: str | None = None) -> rio.MemoryFile:
        """获取属性对应的 Rasterio 栅格图层"""
        data = self.get_raster(attr_name=attr_name)
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
        data = self.get_rasterio()
        out_image, _ = mask.mask(data, [geometry], **kwargs)
        mask_ = out_image.reshape(self.shape)
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

    def has_agent(self) -> np.ndarray:
        """有多少个绑定的主体"""
        return np.vectorize(lambda x: len(x.links))(self.array_cells)

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
        self.cells[agent.pos[0]][agent.pos[1]].remove(agent)
        agent.put_on_layer(self, position)


class BaseNature(CompositeModule, mg.GeoSpace):
    """最主要的自然模块"""

    def __init__(self, model, name="nature", crs=CRS):
        CompositeModule.__init__(self, model, name=name)
        mg.GeoSpace.__init__(self, crs=crs)
