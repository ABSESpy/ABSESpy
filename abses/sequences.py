#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import logging
from collections.abc import Iterable
from numbers import Number
from typing import Any, Callable, Dict, List, Optional, Self, Union

import numpy as np
from agentpy import Agent, AgentList, AttrIter

from .actor import Actor
from .tools.func import make_list, norm_choice

logger = logging.getLogger("__name__")


class ActorsList(AgentList):
    def __repr__(self):
        results = []
        for k, v in self.to_dict().items():
            results.append(f"({len(v)}){k}")
        return f"<{'; '.join(results)}>"

    def __getattr__(self, name) -> np.ndarray:
        """Return callable list of attributes"""
        if name[0] == "_":  # Private variables are looked up normally
            super().__getattr__(name)
        elif name in self.__dir__():
            return super().__getattr__(name)
        else:
            return ActorsList.array(self, name)

    def _is_same_length(self, length: Iterable[Any]) -> bool:
        if not hasattr(self, "__len__"):
            raise ValueError(f"{type(length)} object is not iterable.")
        elif not length.__len__() == self.__len__():
            return False
        else:
            return True

    def to_dict(self) -> Dict[str, Self]:
        dic = {}
        for actor in self.__iter__():
            breed = actor.breed
            if breed not in dic:
                dic[breed] = ActorsList(self.model, [actor])
            else:
                dic[breed].append(actor)
        return dic

    def select(self, selection: Union[str, Iterable[bool]]) -> Self:
        """Returns a new :class:`ActorList` based on `selection`.

        Arguments:
            selection (list of bool): List with same length as the agent list.
                Positions that return True will be selected.
        """
        if isinstance(selection, str):
            return self.to_dict()[selection]
        elif self._is_same_length(selection):
            selected = [a for a, s in zip(self, selection) if s]
            return ActorsList(self.model, selected)
        else:
            raise TypeError(f"Invalid selection {type(selection)}")

    def ids(self, ids: Iterable[int]) -> List[Actor]:
        """
        Select by a `ids` list of Agent.

        Args:
            ids (iterable): an iterable id list. List[id], ID is an attr of agent obj.

        Returns:
            ActorList: A subset of origin agents list.
        """
        ids = make_list(ids)
        agents = self.select([agent.id in ids for agent in self])
        return agents

    def random_choose(
        self,
        p: Optional[Iterable[float]] = None,
        size: int = 1,
        replace: bool = True,
    ) -> Union[Actor, Self]:
        if size == 1:
            return norm_choice(self, p=p, replace=replace)
        elif size > 1:
            chosen = norm_choice(self, p=p, size=size, replace=replace)
            return ActorsList(self.model, chosen)

    def better(
        self, metric: str, than: Optional[Union[Number, Actor]] = None
    ) -> Self:
        metrics = self.array(attr=metric)
        if than is None:
            return self.select(metrics == max(metrics))
        elif isinstance(than, Number):
            return self.select(metrics > than)
        elif isinstance(than, Actor):
            diff = self.diff(metric, than)
            return self.select(diff > 0)

    def diff(self, metric: str, other: Actor) -> np.ndarray:
        diff = self.array(metric) - getattr(other, metric)
        return np.array(diff)

    def update(self, attr: str, values: Iterable[any]) -> None:
        [agent.update(attr, val) for agent, val in zip(self, values)]

    def decision_is(self, decision, rate=False):
        selected = self.select(self.decision.now == decision)
        if rate:
            return len(selected) / len(self)
        else:
            return selected

    def split(self, where: Iterable[int]) -> np.ndarray:
        """
        split agents into N+1 groups.

        Args:
            where (Iterable[int]): indexes [size=N] denotes where to split.

        Returns:
            np.ndarray: N+1 groups: agents array
        """
        to_split = np.array(self)
        return np.hsplit(to_split, where)

    def remove(self, agents: Iterable[Agent]) -> None:
        for agent in make_list(agents):
            super().remove(agent)

    def array(
        self, attr: str, how: "int|str" = "attr", *args, **kwargs
    ) -> np.ndarray:
        if how == "attr":
            results = [getattr(actor, attr) for actor in self]
        elif how == "loc":
            results = self.loc(attr)
        elif how == "mine":
            results = self.mine(attr, *args, **kwargs)
        return np.array(results)

    def position_to_coord(self, x_coords, y_coords):
        X, Y = np.meshgrid(x_coords, y_coords)
        lon = [X[x, y] for x, y in self.pos]
        lat = [Y[x, y] for x, y in self.pos]
        return lon, lat

    def apply(self, func: Callable, *args, **kwargs):
        for actor in self.__iter__():
            yield actor.__getattr__(func)(*args, **kwargs)
