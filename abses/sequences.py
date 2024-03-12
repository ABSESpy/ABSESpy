#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""ActorsList is a sequence of actors.
It's used to manipulate the actors quickly in batch.
"""

from __future__ import annotations

from collections.abc import Iterable
from functools import partial
from numbers import Number
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Union,
    overload,
)

try:
    from typing import Self, TypeAlias
except ImportError:
    from typing_extensions import TypeAlias, Self

import mesa_geo as mg
import numpy as np

from abses.errors import ABSESpyError
from abses.random import ListRandom
from abses.selection import selecting

from .tools.func import make_list

if TYPE_CHECKING:
    from .actor import Actor

Selection: TypeAlias = Union[str, Iterable[bool]]


def get_only_agent(agents: ActorsList) -> Actor:
    """Select one agent"""
    if len(agents) == 0:
        raise ValueError("No agent found.")
    if len(agents) == 1:
        return agents[0]
    raise ValueError("More than one agent.")


def agg_agents_attr(agents: ActorsList, attr, how: str = "only") -> Any:
    """Retrieve the attribute of an either specified or randomly chosen agent."""
    if how == "only":
        return getattr(get_only_agent(agents), attr)
    if how == "random":
        return getattr(np.random.choice(agents), attr)


class ActorsList(list):
    """A list of actors in an agent-based model."""

    def __init__(self, model, objs=()):
        super().__init__(objs)
        self._model = model

    def __repr__(self):
        results = [f"({len(v)}){k}" for k, v in self.to_dict().items()]
        return f"<ActorsList: {'; '.join(results)}>"

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
            ActorsList(self._model, results)
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

    @property
    def random(self) -> ListRandom:
        """随机模块"""
        return ListRandom(actors=self, model=self._model)

    def to_dict(self) -> Dict[str, Self]:
        """Convert all actors in this list to a dictionary like {breed: ActorList}.

        Returns:
            key is the breed of actors, and values are corresponding actors.
        """
        dic = {}
        for actor in iter(self):
            breed = actor.breed
            if breed not in dic:
                dic[breed] = ActorsList(self._model, [actor])
            else:
                dic[breed].append(actor)
        return dic

    def select(self, selection: Selection) -> Self:
        """
        Returns a new :class:`ActorList` based on `selection`.

        Parameters:
            selection:
                List with same length as the agent list.
                Positions that return True will be selected.
        """
        if isinstance(selection, (str, dict)):
            bool_ = [selecting(actor, selection) for actor in self]
        elif isinstance(selection, (list, tuple, np.ndarray)):
            bool_ = make_list(selection)
        else:
            raise TypeError(f"Invalid selection type {type(selection)}")
        selected = [a for a, s in zip(self, bool_) if s]
        return ActorsList(self._model, selected)

    def ids(self, ids: Iterable[int]) -> List[Actor]:
        """Subsets ActorsList by a `ids`.

        Parameters:
            ids:
                an iterable id list. List[id], ID is an attr of agent obj.

        Returns:
            ActorList: A subset of origin agents list.
        """
        ids = make_list(ids)
        return self.select([agent.id in ids for agent in self])

    def better(
        self, metric: str, than: Optional[Union[Number, Actor]] = None
    ) -> Self:
        """
        Selects the elements of the sequence that are better than a given value or actor
        based on a specified metric.

        Parameters:
            metric:
                The name of the attribute to use as the metric for comparison.
            than:
                The value or actor to compare against. If None, selects the elements with the
                highest value for the specified metric. If a number, selects the elements with
                a value greater than the specified number. If an Actor, selects the elements
                with a value greater than the specified Actor's value for the specified metric.

        Returns:
            A new sequence containing the selected elements.

        Raises:
            ABSESpyError:
                If the `than` parameter is not a Number or an Actor.

        Notes:
            This method compares the values of the specified metric for all elements in the
            sequence and selects the elements that are better than the specified value or actor.
            The comparison is based on the greater than operator (>) for numbers and the
            difference between the values for actors.
        """
        metrics = self.array(attr=metric)
        if than is None:
            return self.select(metrics == max(metrics))
        if isinstance(than, Number):
            return self.select(metrics > than)
        if isinstance(than, mg.GeoAgent):
            diff = self.array(metric) - getattr(than, metric)
            return self.select(diff > 0)
        raise ABSESpyError(f"Invalid than type {type(than)}.")

    def update(self, attr: str, values: Iterable[any]) -> None:
        """Update the specified attribute of each agent in the sequence with the corresponding value in the given iterable.

        Parameters:
            attr:
                The name of the attribute to update.
            values:
                An iterable of values to update the attribute with. Must be the same length as the sequence.

        Raises:
            ValueError:
                If the length of the values iterable does not match the length of the sequence.
        """
        self._is_same_length(values, rep_error=True)
        for agent, val in zip(self, values):
            setattr(agent, attr, val)

    def split(self, where: Iterable[int]) -> np.ndarray:
        """Split agents into N+1 groups.

        Parameters:
            where:
                indexes [size=N] denotes where to split.

        Returns:
            np.ndarray: N+1 groups: agents array
        """
        to_split = np.array(self)
        return np.hsplit(to_split, where)

    def array(self, attr: str) -> np.ndarray:
        """Convert the specified attribute of all actors to a numpy array.

        Parameters:
            attr:
                The name of the attribute to convert to a numpy array.

        Returns:
            A numpy array containing the specified attribute of all actors.
        """
        return np.array([getattr(actor, attr) for actor in self])

    def trigger(self, func_name: str, *args: Any, **kwargs: Any) -> np.ndarray:
        """Call a method with the given name on all actors in the sequence.

        Parameters:
            func_name:
                The name of the method to call on each actor.
            *args:
                Positional arguments to pass to the method.
            **kwargs:
                Keyword arguments to pass to the method.

        Returns:
            An array of the results of calling the method on each actor.
        """
        results = [
            getattr(actor, func_name)(*args, **kwargs) for actor in iter(self)
        ]
        return np.array(results)

    def apply(self, ufunc: Callable, *args: Any, **kwargs: Any) -> np.ndarray:
        """Apply ufunc to all actors in the sequence.

        Parameters:
            ufunc:
                The function to apply to each actor.
            *args:
                Positional arguments to pass to the function.
            **kwargs:
                Keyword arguments to pass to the function.

        Returns:
            An array of the results of applying the function to each actor.
        """
        func = partial(ufunc, *args, **kwargs)
        return np.array(list(map(func, self)))
