#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

import mesa_geo as mg

from abses import Actor, ActorsList
from abses.links import LinkNode
from abses.sequences import agg_agents_attr

if TYPE_CHECKING:
    from abses.nature import PatchModule


def raster_attribute(func):
    """将方法变为斑块可以提取的属性"""
    func.is_decorated = True
    return property(func)


class PatchCell(mg.Cell, LinkNode):
    """斑块"""

    def __init__(self, pos=None, indices=None):
        mg.Cell.__init__(self, pos, indices)
        LinkNode.__init__(self)
        self._agents = {}
        self._layer = None

    def __repr__(self) -> str:
        return f"<PatchCell at {self.pos}>"

    @classmethod
    def __attribute_properties__(cls) -> set[str]:
        """属性"""
        return {
            name
            for name, method in cls.__dict__.items()
            if isinstance(method, property)
            and getattr(method.fget, "is_decorated", False)
        }

    @property
    def layer(self) -> PatchModule:
        """所在图层"""
        return self._layer

    @layer.setter
    def layer(self, layer: PatchModule) -> None:
        """设置图层"""
        if not isinstance(layer, mg.RasterLayer):
            raise TypeError(f"{type(layer)} is not valid layer.")
        self.container = layer.model.human
        self._layer = layer

    @classmethod
    @property
    def breed(cls) -> str:
        """种类"""
        return cls.__name__

    def has_agent(self, breed: Optional[str] = None) -> bool:
        """当前位置是否站着行动者"""
        return bool(self._agents) if breed is None else breed in self._agents

    @property
    def agents(self) -> ActorsList:
        """该斑块上的所有主体"""
        agents = []
        for _, agents_set in self._agents.items():
            agents.extend(agents_set)
        return ActorsList(self.model, agents)

    def get_attr(self, attr_name: str) -> Any:
        """获取某个属性，如果是图层的动态数据，则先自动更新
        AttributeError: Attribute value of the associated patch cell.
        """
        if attr_name in self.layer.dynamic_variables:
            self.layer.dynamic_var(attr_name=attr_name)
        if not hasattr(self, attr_name):
            raise AttributeError(f"{attr_name} not exists in {self.layer}.")
        return getattr(self, attr_name)

    def add(self, agent: Actor) -> None:
        """将一个主体添加到该处"""
        if agent.on_earth:
            raise ValueError(f"{agent} is already on earth.")
        if agent.breed not in self._agents:
            self._agents[agent.breed] = {agent}
        else:
            self._agents[agent.breed].add(agent)

    def remove(self, agent: Actor) -> None:
        """将一个此处的主体移除"""
        try:
            self._agents[agent.breed].remove(agent)
        except KeyError as err:
            raise KeyError(f"{agent} is not on {self}.") from err
        agent.put_on()
        if not self._agents[agent.breed]:
            del self._agents[agent.breed]

    def linked(self, link: str) -> ActorsList:
        """获取链接到该斑块的主体"""
        if link is None:
            return self.agents
        elif not isinstance(link, str):
            raise TypeError(f"{type(link)} is not valid link name.")
        elif link not in self.links:
            raise KeyError(f"{link} not exists in {self}.")
        else:
            agents = ActorsList(self.model, super().linked(link=link))
        return agents

    def linked_attr(
        self,
        attr: str,
        link: Optional[str] = None,
        nodata: Any = None,
        how: str = "only",
    ) -> Any:
        """获取链接到该斑块的主体的属性"""
        try:
            agents = self.linked(link=link)
        except KeyError:
            agents = ActorsList(self.model, [])
        if nodata is None or agents:
            return agg_agents_attr(agents=agents, attr=attr, how=how)
        return nodata

    def get_neighboring_cells(
        self,
        moore: bool = False,
        radius: int = 1,
        include_center: bool = False,
        annular: bool = False,
    ) -> ActorsList:
        """获取该斑块周围的格子"""
        cells = self.layer.get_neighboring_cells(
            self.pos, moore=moore, radius=radius, include_center=include_center
        )
        if annular:
            interiors = self.layer.get_neighboring_cells(
                self.pos, moore=moore, radius=radius - 1, include_center=False
            )
            return ActorsList(self.model, set(cells) - set(interiors))
        return ActorsList(self.model, cells)
