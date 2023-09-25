#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/
from __future__ import annotations

import logging
import uuid
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Self,
    Set,
    Tuple,
    TypeAlias,
    Union,
)

import mesa
import mesa_geo as mg
from mesa.space import Coordinate
from omegaconf import DictConfig
from shapely import Point

from abses.sequences import ActorsList

from .objects import BaseObj

# A class that is used to store the position of the agent.


if TYPE_CHECKING:
    from abses.nature import PatchCell

    from .main import MainMediator

Selection: TypeAlias = Union[str, Iterable[bool]]
Trigger: TypeAlias = Union[Callable, str]

logger = logging.getLogger("__name__")


def parsing_string_selection(selection: str) -> Dict[str, Any]:
    """解析字符串检索式"""
    selection_dict = {}
    if "==" not in selection:
        return {"breed": selection}
    expressions = selection.split(",")
    for exp in expressions:
        left, right = tuple(exp.split("=="))
        selection_dict[left.strip(" ")] = right.strip(" ")
    return selection_dict


def perception(func) -> Callable:
    """感知世界"""

    @property
    def wrapper(self: Actor, *args, **kwargs):
        """感知"""
        return func(self, *args, **kwargs)

    return wrapper


# def check_rule(loop: bool = False) -> Callable:
#     """检查规则"""
#     def f(func: Callable) -> Callable:
#         def wrapper(self: Actor, *args, **kwargs):
#             triggered = self._check_rules("now")
#             if loop:
#                 while len(triggered) > 0:
#                     triggered = self._check_rules("now")
#             return func(self, *args, **kwargs)

#         return wrapper

#     return f


class Actor(BaseObj, mg.GeoAgent):
    """
    社会-生态系统中的行动者
    """

    # when checking the rules
    _freq_levels = {"now": 0, "update": 1, "move": 2, "any": 3}

    def __init__(
        self,
        model,
        observer: bool = True,
        unique_id: Optional[int] = None,
        **kwargs,
    ) -> None:
        if not unique_id:
            unique_id = uuid.uuid4().int
        crs = kwargs.pop("crs", model.nature.crs)
        geometry = kwargs.pop("geometry", None)
        mg.GeoAgent.__init__(
            self, unique_id, model=model, geometry=geometry, crs=crs
        )
        BaseObj.__init__(self, model, observer=observer)
        self._links: Dict[str, Set] = {}
        self._lands: Dict[str, Set] = {}
        self._rules: Dict[str, Dict[str, Any]] = {}
        self._cell: PatchCell = None
        self._layer: mg.RasterLayer = None
        # self.mediator: MainMediator = self.model.mediator

    def put_on(self, cell: PatchCell | None = None) -> None:
        """直接置于某斑块上，或者移除世界"""
        if cell is None:
            # 将这个主体从世界上移除
            self._cell = None
            self._layer = None
            return
        if self.layer and self.layer is not cell.layer:
            raise IndexError(
                f"Trying to move actor between different layers: from {self.layer} to {cell.layer}"
            )
        if not isinstance(cell, mg.Cell):
            raise TypeError(
                f"Actor must be put on a PatchCell, instead of {type(cell)}"
            )
        if self.on_earth:
            self._cell.remove(self)
            self._cell = None
        cell.add(self)
        self._cell = cell
        self._layer = cell.layer
        self.geometry = Point(cell.layer.transform * cell.indices)

    def put_on_layer(self, layer: mg.RasterLayer, pos: Tuple[int, int]):
        """把主体放到某个栅格图层上"""
        if not isinstance(layer, mg.RasterLayer):
            raise TypeError(f"{layer} is not mg.RasterLayer.")
        cell = layer.cells[pos[0]][pos[1]]
        self.put_on(cell=cell)

    @property
    def links(self) -> List[str]:
        """与其他行动者的关系"""
        return list(self._links.keys())

    @property
    def lands(self) -> List[str]:
        """相关的土地类型"""
        return list(self._lands.keys())

    @property
    def indices(self) -> Coordinate:
        """(row, col)形式的坐标，从左上角往下，用于矩阵索引"""
        return self._cell.indices

    @property
    def pos(self) -> Coordinate:
        """(x, y)形式的坐标，从左下角向上，用于cells嵌套列表索引"""
        return self._cell.pos

    @pos.setter
    def pos(self, pos) -> None:
        if pos is not None:
            raise AttributeError(f"Set pos by {self.put_on_layer.__name__}")

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name[0] != "_" and hasattr(self, "_rules"):
            self._check_rules(check_when="any")

    @classmethod
    @property
    def breed(cls) -> str:
        """主体的种类"""
        return cls.__name__

    @property
    def population(self):
        """所有与自己同类的主体"""
        return self.model.agents[self.breed]

    @property
    def on_earth(self) -> bool:
        """是否在世界上有自己的位置"""
        return bool(self._cell)

    @property
    def here(self) -> ActorsList:
        """所有这里的主体"""
        return self._cell.agents

    @property
    def layer(self) -> mg.RasterLayer:
        """所在的栅格图层"""
        return self._layer

    def _freq_level(self, level: str) -> int:
        code = self._freq_levels.get(level)
        if code is None:
            keys = tuple(self._freq_levels.keys())
            raise KeyError(f"freq level {level} is not available in {keys}")
        return code

    def _check_rules(self, check_when: str) -> List[str]:
        triggered_rules = []
        for name in list(self._rules.keys()):
            rule = self._rules[name]
            parameters = rule.get("params", {})
            if rule.frequency < self._freq_level(check_when):
                continue
            if self.selecting(rule.when) is True:
                triggered_rules.append(name)
                # check if is a disposable rule
                if rule.disposable is True:
                    # self.logger.debug(
                    #     f"Rule '{name}' applied on '{self}' in {self.time}."
                    # )
                    del self._rules[name]
                getattr(self, rule.then)(**parameters)
        # delete disposable rules
        return triggered_rules

    def link_to(
        self,
        agent: Self | mg.Cell,
        link: Optional[str] = None,
        mutual: bool = False,
        to_land: bool = False,
    ) -> None:
        """将行动者与其它行动者或地块建立连接"""
        if not isinstance(agent, mesa.Agent):
            raise TypeError(
                f"Agent must be mesa.Agent object, instead of {type(agent)}."
            )
        dictionary = self._lands if to_land else self._links
        if link not in dictionary:
            dictionary[link] = {agent}
        else:
            dictionary[link].add(agent)
        # 相互联系
        if mutual:
            agent.link_to(self, link=link)

    def linked_agents(
        self, link: str, land: bool = False, strict: bool = True
    ) -> ActorsList:
        """获取相关联的所有其它主体"""
        dictionary = self._lands if land else self._links
        if strict and link not in dictionary:
            raise KeyError(
                f"{self} doesn't have any link '{link}' {'[land]' if land else ''}."
            )
        agents_lst = dictionary.get(link, [])
        return ActorsList(model=self.model, objs=agents_lst)

    def selecting(self, selection: Union[str, Dict[str, Any]]) -> bool:
        """根据一定条件选取主体"""
        if isinstance(selection, str):
            selection = parsing_string_selection(selection)
        results = []
        for k, v in selection.items():
            attr = getattr(self, k, None)
            if attr is None:
                results.append(False)
            elif attr == v or str(attr) == v:
                results.append(True)
            else:
                results.append(False)
        return all(results)

    def rule(
        self,
        when: Selection,
        then: Trigger,
        name: Optional[str] = None,
        frequency: str = "any",
        disposable: bool = False,
        check_now: Optional[bool] = True,
        **kwargs,
    ):
        """设置规则，一旦`when`的条件满足，就会触发`then`"""
        if name is None:
            name = f"rule ({len(self._rules) + 1})"
        self._rules[name] = DictConfig(
            {
                "when": when,
                "then": then,
                "params": kwargs,
                "disposable": disposable,
                "frequency": self._freq_level(frequency),
            }
        )
        if check_now is True:
            self._check_rules("now")

    def die(self) -> None:
        """从世界消失"""
        self.model.agents.remove(self)
        if self.on_earth:
            self._cell.remove(self)
            del self

    def move_to(self, position: Optional[Tuple[int, int]]) -> bool:
        """移动到某个位置"""
        if not self._layer:
            raise ValueError("Layer is not set.")
        self._layer.move_agent(self, position)

    def loc(self, attribute: str) -> Any:
        """寻找自己所在位置的斑块数据"""
        return self._cell.get_attr(attribute)

    def alter_nature(self, attr: str, value: Any) -> None:
        """改变自己所在位置的斑块数据"""
        if attr not in self._cell.attributes:
            raise AttributeError(f"Attribute {attr} not found.")
        setattr(self._cell, attr, value)

    # def find_tutor(self, others, metric, how="best"):
    #     better = others.better(metric, than=self)
    #     if len(better) == 0:
    #         tutor = self
    #     else:
    #         if how == "best":
    #             better = others.better(metric, than=None)
    #             weights = None
    #         elif how == "diff":
    #             diff = better.diff(metric, self)
    #             weights = diff
    #         # elif how == "fermi":
    #         #     diff = better.diff(metric, self)
    #         #     weights = fermi_ruler(diff)
    #         else:
    #             raise ValueError(f"Unknown evolve strategy {how}.")
    #         tutor = better.random_choose(p=weights)
    #     self.tutor.update(tutor)
    #     return tutor


# class LandOwner(Actor):
#     def setup(self):
#         super().setup()
#         self._owned_land: Patch = None
#         self._area: Number = None
#         self.land_neighbors = ActorsList(self.model)

#     @property
#     def area(self):
#         return self._area

#     @property
#     def owned_land(self):
#         return self._owned_land

#     @owned_land.setter
#     def owned_land(self, value: "np.ndarray[bool]|bool"):
#         name = f"land_of_{self.breed}<{self.id}>"
#         self._owned_land = self.model.nature.create_patch(value, name=name)
#         self._area = self.owned_land.sum() * self.owned_land.cell_area

#     @property
#     def __iter_lands__(self):
#         return self.owned_land.cells

#     def residents(self, breed: str = None):
#         return self.model.nature.lookup_agents(self.owned_land, breed=breed)

#     def mine(self, patch: str, apply: callable = None) -> np.ndarray:
#         mine = self.require(patch)[self.owned_land]
#         if apply is not None:
#             return apply(mine)
#         else:
#             return mine

#     def add_connections(self, graph: nx.Graph, agents: Iterable[Actor]):
#         graph.add_edges_from([(self, agent) for agent in agents])

#     def alter_nature(
#         self, patch: str, value: "int|float|bool|Iterable", land=False
#     ) -> None:
#         if land:
#             mask = self.owned_land
#             patch = self.require(patch)
#             patch.update(value, mask=mask)
#         else:
#             super().alter_nature(patch, value)

#     def find_land_neighbors(self, ownerships, graph: nx.Graph = None) -> None:
#         owned = self.owned_land
#         mask = owned.arr.buffer() & ~owned
#         neighbors_id = np.unique(ownerships[mask])
#         neighbors = self.population.ids(neighbors_id)
#         self.land_neighbors.extend(neighbors)
#         self.add_connections(graph, neighbors)

#     def find_tutor(self, metric, others=None, how="best"):
#         if others is None:
#             others = self.land_neighbors
#         return super().find_tutor(others, metric, how)
