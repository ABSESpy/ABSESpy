#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/
from __future__ import annotations

import logging
from numbers import Number
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Self,
    Tuple,
    TypeAlias,
    Union,
    overload,
)

import networkx as nx
import numpy as np
from agentpy import AgentSet, AttrDict

from .objects import BaseObj
from .patch import Patch

if TYPE_CHECKING:
    from .main import MainMediator
    from .sequences import ActorsList

Selection: TypeAlias = Union[str, Iterable[bool]]
Trigger: TypeAlias = Union[Callable, str]

logger = logging.getLogger("__name__")


def parsing_string_selection(selection: str) -> Dict[str, Any]:
    selection_dict = dict()
    if "==" not in selection:
        return {"breed": selection}
    else:
        expressions = selection.split(",")
        for exp in expressions:
            left, right = tuple(exp.split("=="))
            selection_dict[left.strip(" ")] = right.strip(" ")
    return selection_dict


def perception(func):
    @property
    def wrapper(self: Actor, *args, **kwargs):
        return func(self, *args, **kwargs)

    return wrapper


def link_to(func):
    # TODO and links, which can be searched through networkx
    @property
    def wrapper(self: Actor, *args, **kwargs):
        return func(self, *args, **kwargs)

    return wrapper


def check_rule(loop: bool = False) -> Callable:
    def f(func: Callable) -> Callable:
        def wrapper(self: Actor, *args, **kwargs):
            triggered = self._check_rules("now")
            if loop is True:
                while len(triggered) > 0:
                    triggered = self._check_rules("now")
            return func(self, *args, **kwargs)

        return wrapper

    return f


class Actor(BaseObj):
    # when checking the rules
    _freq_levels = {"now": 0, "update": 1, "move": 2, "any": 3}

    def __init__(
        self,
        model,
        observer: bool = True,
        name: Optional[str] = None,
        **kwargs,
    ):
        BaseObj.__init__(self, model, observer=observer, name=name)
        self._on_earth: bool = False
        self._pos: Tuple[int, int] = None
        self._relationships: Dict[str, ActorsList] = AttrDict()
        self._ownerships: Dict[str, Patch] = AttrDict()
        self._rules: Dict[str, Dict[str, Any]] = dict()
        self.mediator: MainMediator = self.model.mediator
        self.setup(**kwargs)

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name[0] != "_" and hasattr(self, "_rules"):
            self._check_rules(check_when="any")

    @classmethod
    @property
    def breed(cls) -> str:
        return cls.__name__

    @property
    def population(self):
        return self.model.agents[self.breed]

    @property
    def on_earth(self) -> bool:
        return self._on_earth

    @property
    def pos(self) -> Tuple[int, int]:
        return self._pos

    @property
    def here(self) -> ActorsList:
        if self.on_earth is True:
            return self.neighbors(0)
        else:
            return None

    def _freq_level(self, level: str) -> int:
        code = self._freq_levels.get(level, None)
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
                    self.logger.debug(
                        f"Rule '{name}' applied on '{self}' in {self.time}."
                    )
                    del self._rules[name]
                self.__getattr__(rule.then)(**parameters)
        # delete disposable rules
        return triggered_rules

    def request(
        self,
        request: str,
        header: Dict[str, Any],
        receiver: Optional[str] = None,
    ) -> Any:
        if receiver is None:
            response = self.mediator.transfer_request(self, request)
        elif receiver in ["nature", "human"]:
            results = self.mediator.trigger_functions(
                users=receiver, func_name=request, **header
            )
            response = results.__getattribute__(receiver)
        else:
            raise ValueError(f"Unknown transfer request {receiver}")
        return response

    # def request(self, request: str, header=None, receiver=None) -> Any:
    #     # header.update({'how': 'GET'})
    #     return self.request(request, header, receiver)

    # def post(self, request: str, value: Any, header=None, receiver=None):
    #     header.update({'how': 'POST', request: value})
    #     return self._request(request, header, receiver)

    def selecting(self, selection: Union[str, Dict[str, Any]]) -> bool:
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
        if name is None:
            name = f"rule ({len(self._rules) + 1})"
        self._rules[name] = AttrDict(
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

    def die(self):
        self.model.agents.remove(self)

    def neighbors(
        self,
        distance: int = 1,
        approach: int = 4,
        selection: Selection = None,
        exclude: bool = True,
    ):
        # The area around within a certain distance.
        header = {
            "pos": self.pos,
            "distance": distance,
            "selection": selection,
            "approach": approach,
        }
        agents = self.request(
            request="neighbors", header=header, receiver="nature"
        )
        if exclude is True:
            agents.remove(self)
        return agents

    def settle_down(self, position: Optional[Tuple[int, int]]) -> bool:
        header = {"actor": self, "position": position}
        self.request("actor_to", header=header, receiver="nature")
        self._pos = position
        self._on_earth = True

    def move(self, pos: Optional[Tuple[int, int]] = None):
        if self.on_earth is False:
            raise ValueError(f"Position of {self} is not set.")
        if pos is None:
            pos = self.request(
                "random_positions", header={"k": 1}, receiver="nature"
            )[0]
        self.settle_down(pos)

    def link_to(self, name: str, other: Union[Self, Iterable[Self], Callable]):
        pass

    def loc(self, request: str, **kwargs):
        header = {"sender": self, "position": self.pos}
        response = self.request(request, header, **kwargs)
        return response
        # elif len(patch_obj.shape) == 3:
        #     return patch_obj[:, self.pos[0], self.pos[1]]

    def alter_nature(self, patch: str, value: "int|float|bool") -> Patch:
        patch = self.require(patch)
        patch[self.pos] = value
        return patch

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
