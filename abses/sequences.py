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
from functools import cached_property, partial
from numbers import Number
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Sized,
    TypeVar,
    Union,
    cast,
    overload,
)

import pandas as pd
from loguru import logger
from pyproj import CRS

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

import geopandas as gpd
import mesa_geo as mg
import numpy as np
from numpy.typing import NDArray

from abses._bases.errors import ABSESpyError
from abses.random import ListRandom
from abses.selection import selecting
from abses.tools.func import make_list
from abses.viz.viz_actors import _VizNodeList

if TYPE_CHECKING:
    from abses._bases.base_container import UniqueID
    from abses.actor import Actor, GeoType, TargetName
    from abses.links import _LinkNode
    from abses.main import MainModel

Selection: TypeAlias = Union[str, Iterable[bool], Dict[str, Any]]
HOW: TypeAlias = Literal["only", "random", "item"]
Link = TypeVar("Link", bound="_LinkNode")


def get_only_agent(agents: ActorsList) -> Actor:
    """Select one agent"""
    if len(agents) == 0:
        raise ValueError("No agent found.")
    if len(agents) == 1:
        return agents[0]
    raise ValueError("More than one agent.")


class ActorsList(List[Link], Generic[Link]):
    """A list of actors in an agent-based model."""

    def __init__(
        self, model: MainModel[Any, Any], objs: Iterable[Link] = ()
    ) -> None:
        super().__init__(objs)
        self._model = model

    def __repr__(self):
        results = [f"({len(v)}){k}" for k, v in self.to_dict().items()]
        return f"<ActorsList: {'; '.join(results)}>"

    def __eq__(self, other: Iterable[Any]) -> bool:
        return (
            all(actor in other for actor in self)
            if self._is_same_length(cast(Sized, other))
            else False
        )

    @overload
    def __getitem__(self, other: int) -> Link:
        ...

    @overload
    def __getitem__(self, index: slice) -> ActorsList[Link]:
        ...

    def __getitem__(self, index):
        results = super().__getitem__(index)
        return (
            ActorsList(self._model, results)
            if isinstance(index, slice)
            else results
        )

    def _is_same_length(self, length: Sized, rep_error: bool = False) -> bool:
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

    @cached_property
    def random(self) -> ListRandom:
        """Random module"""
        return ListRandom(actors=self, model=self._model)

    @cached_property
    def plot(self) -> _VizNodeList:
        """Plotting module"""
        return _VizNodeList(self._model, self)

    def to_dict(self) -> Dict[str, ActorsList[Link]]:
        """Convert all actors in this list to a dictionary like {breed: ActorList}.

        Returns:
            key is the breed of actors, and values are corresponding actors.
        """
        dic: Dict[str, ActorsList[Link]] = {}
        for actor in iter(self):
            breed = actor.breed
            if breed not in dic:
                dic[breed] = ActorsList(self._model, [actor])
            else:
                dic[breed].append(actor)
        return dic

    def _subset(
        self, geo_type: Optional[GeoType | bool] = None
    ) -> ActorsList[Link]:
        """Returns dataset for plotting."""
        if geo_type is None:
            return self
        if isinstance(geo_type, bool):
            selection: Dict[str, Any] = {"on_earth": geo_type}
        elif geo_type in ("Point", "Shape"):
            selection = {"geo_type": geo_type}
        return self.select(selection)

    def select(
        self,
        selection: Optional[Selection] = None,
        geo_type: Optional[GeoType] = None,
    ) -> ActorsList[Link]:
        """
        Returns a new :class:`ActorList` based on `selection`.

        Parameters:
            selection:
                List with same length as the agent list.
                Positions that return True will be selected.
            geo_type:
                Type of Actors' Geometry.

        Returns:
            A subset containing.
        """
        actors = self._subset(geo_type=geo_type)
        if selection is None:
            return actors
        if isinstance(selection, (str, dict)):
            bool_ = [selecting(actor, selection) for actor in actors]
        elif isinstance(selection, (list, tuple, np.ndarray)):
            bool_ = make_list(selection)
        else:
            raise TypeError(f"Invalid selection type {type(selection)}")
        selected = [a for a, s in zip(actors, bool_) if s]
        return ActorsList(self._model, selected)

    def ids(self, ids: Iterable[UniqueID] | UniqueID) -> ActorsList[Link]:
        """Subsets ActorsList by a `ids`.

        Parameters:
            ids:
                an iterable id list. List[id], ID is an attr of agent obj.

        Returns:
            ActorList: A subset of origin agents list.
        """
        ids = make_list(ids)
        return self.select([agent.unique_id in ids for agent in self])

    def better(
        self, metric: str, than: Optional[Union[Number, Actor]] = None
    ) -> ActorsList[Link]:
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

    def update(self, attr: str, values: Iterable[Any]) -> None:
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
        self._is_same_length(cast(Sized, values), rep_error=True)
        for agent, val in zip(self, values):
            setattr(agent, attr, val)

    def split(self, where: NDArray[Any]) -> List[ActorsList[Link]]:
        """Split agents into N+1 groups.

        Parameters:
            where:
                indexes [size=N] denotes where to split.

        Returns:
            np.ndarray: N+1 groups: agents array
        """
        split = np.hsplit(np.array(self), where)
        return [ActorsList(self._model, group) for group in split]

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

    def get(
        self,
        attr: str,
        target: Optional[TargetName] = None,
        how: HOW = "only",
        default: Optional[Any] = None,
    ) -> Any:
        """Retrieve the attribute of an either specified or randomly chosen agent.

        Parameters:
            attr:
                The name of the attribute to retrieve.
            how:
                The method to use to retrieve the attribute. Can be either "only" or "random".

        Returns:
            The attribute of the specified agent.
        """
        if agent := self.item(how=how, index=0):
            return agent.get(attr, target=target)
        if default is not None:
            return default
        raise ValueError("No agent found or default value.")

    def set(
        self, attr: str, value: Any, target: Optional[TargetName] = None
    ) -> None:
        """Set the attribute of all agents in the sequence to the specified value.

        Parameters:
            attr:
                The name of the attribute to set.
            value:
                The value to set the attribute to.
        """
        for agent in iter(self):
            agent.set(attr, value, target=target)

    def item(self, how: HOW = "item", index: int = 0) -> Optional[Link]:
        """Retrieve one agent if possible.

        Parameters:
            how:
                The method to use to retrieve the agent.
                Can be either "only", "item", or "random".
                If "only", it will return the only agent in the container.
                In this case, the container must have only one agent.
                If more than one or no agent is found, it will raise an error.
                If "item", it will return the agent at the given index.
                If "random", it will return a randomly chosen agent.
            index:
                The index of the agent to retrieve.

        Returns:
            The agent if found, otherwise None.
        """
        if how == "only":
            return get_only_agent(self)
        if how == "random":
            actor = self.random.choice(when_empty="return None")
            return cast(Optional["Actor"], actor)
        if how == "item":
            return self[index] if len(self) > index else None
        raise ValueError(f"Invalid how method '{how}'.")

    def _check_crs_consistent(self) -> CRS:
        crs_set = set(self.array("crs"))
        if None in crs_set:
            logger.warning("Some agents don't have a crs.")
            crs_set.remove(None)
        if len(crs_set) > 1:
            raise ValueError(f"More than one crs: {crs_set}.")
        if not crs_set:
            logger.warning("No crs when init a GeoDataFrame.")
        return crs_set.pop()

    @overload
    def summary(self, geometry: bool = True, **kwargs) -> gpd.GeoDataFrame:
        ...

    @overload
    def summary(self, geometry: bool = False, **kwargs) -> pd.DataFrame:
        ...

    def summary(
        self, geometry: bool = False, **kwargs
    ) -> pd.DataFrame | gpd.GeoDataFrame:
        """Returns a summarized dataframe of the actors."""
        if len(self) == 0:
            raise ValueError("No actors to retrieve summary information.")
        df = pd.concat([actor.summary(**kwargs) for actor in self], axis=1).T
        if geometry:
            crs = self._check_crs_consistent()
            df["geometry"] = self.array("geometry")
            return gpd.GeoDataFrame(df, geometry="geometry", crs=crs)
        return df
