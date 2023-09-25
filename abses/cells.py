#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from numbers import Number
from typing import TYPE_CHECKING, Any, List, Optional

import mesa_geo as mg
import numpy as np

from abses import Actor, ActorsList

if TYPE_CHECKING:
    from abses.nature import PatchModule


class PatchCell(mg.Cell):
    """斑块"""

    def __init__(self, pos=None, indices=None):
        super().__init__(pos, indices)
        self._attached_agents = {}
        self._agents = {}
        self._layer = None

    def __repr__(self) -> str:
        return f"<PatchCell at {self.pos}>"

    @property
    def layer(self) -> PatchModule:
        """所在图层"""
        return self._layer

    @layer.setter
    def layer(self, layer: PatchModule) -> None:
        """设置图层"""
        if not isinstance(layer, mg.RasterLayer):
            raise TypeError(f"{type(layer)} is not valid layer.")
        self._layer = layer

    @classmethod
    @property
    def breed(cls) -> str:
        """种类"""
        return cls.__name__

    @property
    def links(self) -> List[str]:
        """所有关联类型"""
        return list(self._attached_agents.keys())

    @property
    def has_agent(self) -> bool:
        """当前位置是否站着行动者"""
        return bool(self.agents)

    @property
    def agents(self) -> ActorsList:
        """该斑块上的所有主体"""
        agents = []
        for _, agents_set in self._agents.items():
            agents.extend(agents_set)
        return ActorsList(self.model, agents)

    def get_attr(self, attr_name: str) -> Any:
        """获取某个属性，如果是图层的动态数据，则先自动更新"""
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
        agent.link_to(self, link=link)

    def detach(self, label: str) -> None:
        """取消某个主体与该斑块的联系"""
        if label not in self.links:
            raise KeyError(f"{label} is not a registered link.")
        del self._attached_agents[label]

    def linked(
        self, link: str, nodata: Optional[Any] = None, strict: bool = False
    ) -> Actor:
        """获取链接到该斑块的主体"""
        if strict and link not in self.links:
            raise KeyError(f"Link {link} not exists in {self.links}.")
        return self._attached_agents.get(link, nodata)

    def linked_attr(
        self,
        attr,
        link: Optional[str] = None,
        nodata: Any = np.nan,
        strict: bool = False,
    ) -> Any:
        """获取链接到该斑块的主体的属性"""
        if link in self._agents:
            # TODO 之后应该加入主体上限集合
            # 说明这是一个主体，先获取其属性，目前只取第一个主体
            return getattr(list(self._agents[link])[0], attr)
        if not link and not self.links:
            raise KeyError("No link exists.")
        if not link:
            link = self.links[0]
        agent = self.linked(link=link, strict=strict)
        if not agent:
            return nodata
        if not hasattr(agent, attr):
            raise AttributeError(f"{agent} has no attribute {attr}.")
        value = getattr(agent, attr)
        if not isinstance(value, Number):
            raise TypeError(f"Attribute {attr} is not number.")
        return value
