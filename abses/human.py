#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Optional,
    Set,
    Type,
    Union,
)

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

from abses.actor import Actor
from abses.links import _LinkContainer

from ._bases.modules import CompositeModule, Module
from .cells import PatchCell
from .container import _AgentsContainer
from .sequences import ActorsList, Selection

Actors: TypeAlias = Union[ActorsList[Actor], Selection, Actor]
Trigger: TypeAlias = Union[str, Callable[..., Any]]
if TYPE_CHECKING:
    from abses import MainModel


class HumanModule(Module):
    """The `Human` sub-module base class.

    Note:
        Look at [this tutorial](../tutorial/beginner/organize_model_structure.ipynb) to understand the model structure.

    Attributes:
        agents:
            The agents container of this ABSESpy model.
        collections:
            Actor collections defined.
    """

    def __init__(self, model: MainModel[Any, Any], name: Optional[str] = None):
        Module.__init__(self, model, name)
        self._refers: Dict[str, Dict[str, Any]] = {}

    @property
    def agents(self) -> _AgentsContainer:
        """The agents container of this ABSESpy model."""
        return self.model.agents

    @property
    def collections(self) -> Set[str]:
        """Actor collections defined."""
        return set(self._refers.keys())

    def actors(self, name: Optional[str] = None) -> ActorsList[Actor]:
        """Different selections of agents"""
        if name is None:
            return ActorsList(model=self.model, objs=self.agents)
        if name not in self._refers:
            raise KeyError(f"{name} is not defined.")
        selection = self._refers[name]
        return self.agents.select(**selection)

    def define(
        self,
        refer_name: str,
        **kwargs,
    ) -> ActorsList[Actor]:
        """Define a query of actors and save it into collections.

        Parameters:
            name:
                defined name of this group of actors.
            selection:
                Selection query of `Actor`.

        Raises:
            KeyError:
                If the name is already defined.

        Returns:
            The list of actors who are satisfied the query condition.

        Example:
            ```
            # Create 5 actors to query
            model=MainModel()
            model.agents.new(Actor, 5)

            module = HumanModule(model=model)
            actors = module.define(name='first', selection='ids=0')
            >>> len(actors)
            >>> 1

            >>> module.actors('first') == actors
            >>> True
            ```
        """
        if refer_name in self._refers:
            raise KeyError(f"{refer_name} is already defined.")
        selected = self.agents.select(**kwargs)
        self._refers[refer_name] = kwargs.copy()
        return selected


class BaseHuman(CompositeModule, HumanModule, _LinkContainer):
    """The Base Human Module."""

    def __init__(self, model: MainModel[Any, Any], name: str = "human"):
        HumanModule.__init__(self, model, name)
        CompositeModule.__init__(self, model, name=name)
        _LinkContainer.__init__(self)
