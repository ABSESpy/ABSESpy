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
    """
    A list of actors in an agent-based model.

    Parameters
    ----------
    model : Model
        The agent-based model that this list belongs to.
    objs : iterable, optional
        The initial actors to add to the list. Defaults to an empty list.

    Attributes
    ----------
    _model : Model
        The agent-based model that this list belongs to.

    Methods
    -------
    __getattr__(self, name: str) -> np.ndarray:
        Return callable list of attributes.
    __eq__(self, other: Iterable) -> bool:
        Check if two actor lists are equal.
    __getitem__(self, index) -> Union[Actor, Self]:
        Get an actor or a subset of actors from the list.
    __repr__(self) -> str:
        Return a string representation of the list.
    _is_same_length(self, length: Iterable[Any], rep_error: bool = False) -> bool:
        Check if the length of input is as same as the number of actors.
    to_dict(self) -> Dict[str, Self]:
        Convert all actors in this list to a dictionary.
    select(self, selection: Selection) -> Self:
        Returns a new :class:`ActorList` based on `selection`.
    ids(self, ids: Iterable[int]) -> List[Actor]:
        Subsets ActorsList by a `ids`.
    random_choose(
        self,
        size: int = 1,
        prob: Optional[Iterable[float]] = None,
        replace: bool = True,
        as_list: bool = False,
    ) -> Union[Actor, Self]:
        Randomly choose one or more actors from the current self object.
    better(
        self, metric: str, than: Optional[Union[Number, Actor]] = None
    ) -> Self:
        Selects the elements of the sequence that are better than a given value or actor
        based on a specified metric.
    """

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

        Returns
        -------
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
        """
        Returns a new :class:`ActorList` based on `selection`.

        Parameters
        ----------
        selection : list of bool
            List with same length as the agent list.
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

    def ids(self, ids: Iterable[int]) -> List[Actor]:
        """
        Subsets ActorsList by a `ids`.

        Parameters
        ----------
        ids : iterable
            an iterable id list. List[id], ID is an attr of agent obj.

        Returns
        -------
        ActorList: A subset of origin agents list.
        """
        ids = make_list(ids)
        return self.select([agent.id in ids for agent in self])

    def random_choose(
        self,
        size: int = 1,
        prob: Optional[Iterable[float]] = None,
        replace: bool = True,
        as_list: bool = False,
    ) -> Union[Actor, Self]:
        """
        Randomly choose one or more actors from the current self object.

        Parameters
        ----------
        size: int
            The number of actors to choose. Defaults to 1.
        prob : Optional[Iterable[float]]
            A list of probabilities for each actor to be chosen.
            If None, all actors have equal probability. Defaults to None.
        replace : bool
            Whether to sample with replacement. Defaults to True.
        as_list : bool
            Whether to return the result as a list of actors. Defaults to False.

        Returns
        -------
        Union[Actor, Self]

        Notes
        -----
        Given the parameter set size=1 and as_list=False, a single Actor object is returned.
        Given the parameter set size>1 and as_list=False, a Self (ActorsList) object is returned.

        Raises
        ------
        ValueError: If size is not a positive integer.
        """
        chosen = norm_choice(self, p=prob, size=size, replace=replace)
        if as_list:
            return ActorsList(self.model, objs=chosen)
        if size == 1:
            return chosen[0]
        if size > 1:
            return ActorsList(self.model, chosen)
        raise ValueError(f"Invalid size {size}.")

    def better(
        self, metric: str, than: Optional[Union[Number, Actor]] = None
    ) -> Self:
        """
        Selects the elements of the sequence that are better than a given value or actor
        based on a specified metric.

        Parameters
        ----------
        metric : str
            The name of the attribute to use as the metric for comparison.
        than : {Number, Actor}, optional
            The value or actor to compare against. If None, selects the elements with the
            highest value for the specified metric. If a number, selects the elements with
            a value greater than the specified number. If an Actor, selects the elements
            with a value greater than the specified Actor's value for the specified metric.

        Returns
        -------
        Self
            A new sequence containing the selected elements.

        Raises
        ------
        ValueError
            If the `than` parameter is not a Number or an Actor.

        Notes
        -----
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
        raise ValueError(f"Invalid than type {type(than)}.")

    def update(self, attr: str, values: Iterable[any]) -> None:
        """
        Update the specified attribute of each agent in the sequence with the corresponding value in the given iterable.

        Parameters
        ----------
        attr : str
            The name of the attribute to update.
        values : Iterable[any]
            An iterable of values to update the attribute with. Must be the same length as the sequence.

        Raises
        ------
        ValueError
            If the length of the values iterable does not match the length of the sequence.

        Returns
        -------
        None
        """
        self._is_same_length(values, rep_error=True)
        for agent, val in zip(self, values):
            setattr(agent, attr, val)

    def split(self, where: Iterable[int]) -> np.ndarray:
        """
        Split agents into N+1 groups.

        Parameters
        ----------
        where: Iterable[int]
            indexes [size=N] denotes where to split.

        Returns
        -------
        np.ndarray: N+1 groups: agents array
        """
        to_split = np.array(self)
        return np.hsplit(to_split, where)

    def array(self, attr: str) -> np.ndarray:
        """
        Convert the specified attribute of all actors to a numpy array.

        Parameters
        ----------
        attr : str
            The name of the attribute to convert to a numpy array.

        Returns
        -------
        np.ndarray
            A numpy array containing the specified attribute of all actors.
        """
        return np.array([getattr(actor, attr) for actor in self])

    def trigger(self, func_name: str, *args, **kwargs) -> np.ndarray:
        """
        Call a method with the given name on all actors in the sequence.

        Parameters
        ----------
        func_name : str
            The name of the method to call on each actor.
        *args
            Positional arguments to pass to the method.
        **kwargs
            Keyword arguments to pass to the method.

        Returns
        -------
        np.ndarray
            An array of the results of calling the method on each actor.
        """
        results = [
            getattr(actor, func_name)(*args, **kwargs) for actor in iter(self)
        ]
        return np.array(results)
