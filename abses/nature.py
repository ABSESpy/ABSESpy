#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Self

import mesa_geo as mg
import numpy as np
from mesa.space import Coordinate
from nptyping import NDArray

from .modules import CompositeModule, Module
from .sequences import ActorsList
from .tools.func import norm_choice

if TYPE_CHECKING:
    from abses.actor import Actor

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

    def linked(self, link: str) -> Actor:
        """获取链接到该斑块的主体"""
        if link not in self.links:
            raise KeyError(f"Link {link} not exists in {self.links}.")
        return self._attached_agents[link]


class PatchModule(Module, mg.RasterLayer):
    """基础的空间模块"""

    def __init__(self, model, name=None, **kwargs):
        Module.__init__(self, model, name=name)
        mg.RasterLayer.__init__(self, **kwargs)

    @property
    def shape(self) -> Coordinate:
        """形状"""
        return self.width, self.height

    @property
    def array_cells(self) -> NDArray:
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

    def _attr_or_array(self, data: None | str | np.ndarray) -> np.ndarray:
        if data is None:
            return np.ones(self.shape)
        if isinstance(data, np.ndarray) and data.shape == self.shape:
            return data
        if isinstance(data, str) and data in self.attributes:
            return self.get_raster(data)
        raise TypeError("Invalid data type or shape.")

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
        mask = self._attr_or_array(where)
        cells = self.array_cells[mask]
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
