#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Set, Union

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

from loguru import logger

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
        logger.info("Initializing a new Human Module...")
        self._collections: Dict[str, Selection] = {}

    @property
    def agents(self) -> _AgentsContainer:
        """The agents container of this ABSESpy model."""
        return self.model.agents

    @property
    def collections(self) -> Set[str]:
        """Actor collections defined."""
        return set(self._collections.keys())

    def actors(self, name: Optional[str] = None) -> ActorsList[Actor]:
        """Different selections of agents"""
        if name is None:
            return self.agents.get()
        if name not in self._collections:
            raise KeyError(f"{name} is not defined.")
        selection = self._collections[name]
        return self.actors().select(selection)

    def _must_be_actor(self, actor: Actor) -> None:
        if not isinstance(actor, Actor):
            raise TypeError(
                f"Actor must be a subclass of Actor, instead of {type(actor)}."
            )

    def _must_be_cell(self, cell: PatchCell) -> None:
        if not isinstance(cell, PatchCell):
            raise TypeError(
                f"Cell must be a subclass of Cell, instead of {type(cell)}."
            )

    def define(self, name: str, selection: Selection) -> ActorsList[Actor]:
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
        if name in self._collections:
            raise KeyError(f"{name} is already defined.")
        selected = self.actors().select(selection)
        self._collections[name] = selection
        return selected


class BaseHuman(CompositeModule, HumanModule, _LinkContainer):
    """The Base Human Module."""

    def __init__(self, model: MainModel[Any, Any], name: str = "human"):
        HumanModule.__init__(self, model, name)
        CompositeModule.__init__(self, model, name=name)
        _LinkContainer.__init__(self)
