#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

import logging
from collections.abc import Iterable
from numbers import Number
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Optional,
    Self,
    TypeAlias,
    Union,
    overload,
)

import mesa_geo as mg
import numpy as np

from .tools.func import make_list, norm_choice

if TYPE_CHECKING:
    from .actor import Actor

logger = logging.getLogger("__name__")

Selection: TypeAlias = Union[str, Iterable[bool]]


class ActorsList(list):
    """主体列表"""

    def __init__(self, model, objs=()):
        super().__init__(objs)
        self._model = model

    def __repr__(self):
        results = [f"({len(v)}){k}" for k, v in self.to_dict().items()]
        return f"<ActorsList: {'; '.join(results)}>"

    def __getattr__(self, name: str) -> np.ndarray:
        """Return callable list of attributes"""
        # Private variables are looked up normally
        if name[0] == "_":
            return getattr(super(), name)
        if name in self.__dir__():
            return getattr(super(), name)
        return ActorsList.array(self, name)

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
        if len(length) != len(self):
            if rep_error:
                raise ValueError(
                    f"Length of the input {len(length)} mismatch {len(self)} actors."
                )
            return False
        return True

    def to_dict(self) -> Dict[str, Self]:
        """
        Convert all actors in this list to a dictionary.

        Returns:
            Dict[str, Self]: key is the breed of actors, and values are corresponding actors.
        """
        dic = {}
        for actor in iter(self):
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
        size: int = 1,
        prob: Optional[Iterable[float]] = None,
        replace: bool = True,
    ) -> Union[Actor, Self]:
        """从主体中随机选择一个或多个。"""
        if size == 1:
            return norm_choice(self, p=prob, replace=replace)
        if size > 1:
            chosen = norm_choice(self, p=prob, size=size, replace=replace)
            return ActorsList(self.model, chosen)
        raise ValueError(f"Invalid size {size}.")

    def better(
        self, metric: str, than: Optional[Union[Number, Actor]] = None
    ) -> Self:
        """对比所有主体的某个属性的值。"""
        metrics = self.array(attr=metric)
        if than is None:
            return self.select(metrics == max(metrics))
        if isinstance(than, Number):
            return self.select(metrics > than)
        if isinstance(than, mg.GeoAgent):
            diff = self.array(metric) - getattr(than, metric)
            return self.select(diff > 0)
        raise ValueError(f"Invalid than type {type(than)}.")

    def update(self, attr: str, values: Iterable[any]) -> None:
        """批量更新主体的属性"""
        self._is_same_length(values, rep_error=True)
        for agent, val in zip(self, values):
            setattr(agent, attr, val)

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

    def array(self, attr: str) -> np.ndarray:
        """将所有主体的属性转换为数组"""
        return np.array([getattr(actor, attr) for actor in self])

    def trigger(self, func_name: str, *args, **kwargs) -> np.ndarray:
        """触发列表内所有主体的某个方法"""
        results = [
            getattr(actor, func_name)(*args, **kwargs) for actor in iter(self)
        ]
        return np.array(results)
