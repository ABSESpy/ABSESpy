#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import logging
from collections.abc import Iterable
from numbers import Number
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Self,
    TypeAlias,
    Union,
    overload,
)

import numpy as np
from agentpy import AgentList

from .actor import Actor
from .tools.func import make_list, norm_choice

logger = logging.getLogger("__name__")

Selection: TypeAlias = Union[str, Iterable[bool]]


class ActorsList(AgentList):
    def __repr__(self):
        results = [f"({len(v)}){k}" for k, v in self.to_dict().items()]
        return f"<ActorsList: {'; '.join(results)}>"

    def __getattr__(self, name: str) -> np.ndarray:
        """Return callable list of attributes"""
        if name[0] == "_":  # Private variables are looked up normally
            super().__getattr__(name)
        elif name in self.__dir__():
            return super().__getattr__(name)
        elif len(self) and hasattr(getattr(self[0], name, None), "__call__"):
            return super().__getattr__(name)
        else:
            return ActorsList.array(self, name)

    def __iter__(self) -> Iterator[Actor]:
        return super().__iter__()

    def __eq__(self, other: Iterable) -> bool:
        return (
            all(actor in other for actor in self)
            if self._is_same_length(other)
            else False
        )

    @overload
    def __getitem__(self, other: int) -> Actor:
        ...

    @overload
    def __getitem__(self, index: slice) -> Self:
        ...

    def __getitem__(self, index):
        results = super().__getitem__(index)
        return (
            ActorsList(self.model, results)
            if isinstance(index, slice)
            else results
        )

    def _is_same_length(
        self, length: Iterable[Any], rep_error: bool = False
    ) -> bool:
        """Check if the length of input is as same as the number of actors."""
        if not hasattr(self, "__len__"):
            raise ValueError(f"{type(length)} object is not iterable.")
        elif length.__len__() != self.__len__():
            if rep_error:
                raise ValueError(
                    f"Length of the input {len(length)} mismatch {len(self)} actors."
                )
            return False
        else:
            return True

    def to_dict(self) -> Dict[str, Self]:
        """
        Convert all actors in this list to a dictionary.

        Returns:
            Dict[str, Self]: key is the breed of actors, and values are corresponding actors.
        """
        dic = {}
        for actor in self.__iter__():
            breed = actor.breed
            if breed not in dic:
                dic[breed] = ActorsList(self.model, [actor])
            else:
                dic[breed].append(actor)
        return dic

    def select(self, selection: Selection) -> Self:
        """Returns a new :class:`ActorList` based on `selection`.

        Arguments:
            selection (list of bool): List with same length as the agent list.
                Positions that return True will be selected.
        """
        if isinstance(selection, (str, dict)):
            bool_ = [actor.selecting(selection) for actor in self]
        elif isinstance(selection, (list, tuple, np.ndarray)):
            bool_ = make_list(selection)
        else:
            raise TypeError(f"Invalid selection type {type(selection)}")
        selected = [a for a, s in zip(self, bool_) if s]
        return ActorsList(self.model, selected)

    def now(self) -> Self:
        """Only select actors who is already setup on the earth."""
        return self.select(self.on_earth)

    def ids(self, ids: Iterable[int]) -> List[Actor]:
        """
        Select by a `ids` list of Agent.

        Args:
            ids (iterable): an iterable id list. List[id], ID is an attr of agent obj.

        Returns:
            ActorList: A subset of origin agents list.
        """
        ids = make_list(ids)
        return self.select([agent.id in ids for agent in self])

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
            diff = self.array(metric) - getattr(than, metric)
            return self.select(diff > 0)

    def update(self, attr: str, values: Iterable[any]) -> None:
        self._is_same_length(values, rep_error=True)
        [agent.__setattr__(attr, val) for agent, val in zip(self, values)]

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

    def array(
        self, attr: str, how: "int|str" = "attr", *args, **kwargs
    ) -> np.ndarray:
        if how == "attr":
            results = [getattr(actor, attr) for actor in self]
        # elif how == "loc":
        #     results = self.loc(attr)
        # elif how == "mine":
        #     results = self.mine(attr, *args, **kwargs)
        # TODO: fixing cannot access local variable 'results' where it is not associated with a value
        return np.array(results)

    def position_to_coord(self, x_coords, y_coords):
        # TODO move this to actor's property
        X, Y = np.meshgrid(x_coords, y_coords)
        lon = [X[x, y] for x, y in self.pos]
        lat = [Y[x, y] for x, y in self.pos]
        return lon, lat

    def trigger(self, func_name: str, *args, **kwargs) -> np.ndarray:
        results = [
            getattr(actor, func_name)(*args, **kwargs)
            for actor in self.__iter__()
        ]
        return np.array(results)
