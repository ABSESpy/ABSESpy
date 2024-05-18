#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""Base container, common methods for both the main model and the cells.
"""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterable,
    Optional,
    Type,
    Union,
)

import numpy as np
import pyproj

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

from abses._bases.errors import ABSESpyError
from abses.actor import Actor, Breeds
from abses.sequences import HOW, ActorsList, Selection
from abses.tools.func import make_list

if TYPE_CHECKING:
    from abses.main import MainModel

ActorTypes: TypeAlias = Union[Type[Actor], Iterable[Type[Actor]]]
Actors: TypeAlias = Union[Actor, ActorsList, Iterable[Actor]]
UniqueID: TypeAlias = Union[str, int]


class _AgentsContainer(dict):
    """AgentsContainer for the main model."""

    def __init__(
        self,
        model: MainModel[Any, Any],
        max_len: None | int = None,
    ):
        super().__init__({b: set() for b in model.breeds})
        self._model: MainModel = model
        model._containers.append(self)
        self._max_length: Optional[int] = max_len

    def __len__(self) -> int:
        return len(self.get())

    def __str__(self) -> str:
        return "ModelAgents"

    def __repr__(self) -> str:
        strings = [f"({len(v)}){k}" for k, v in self.items()]
        return f"<{str(self)}: {'; '.join(strings)}>"

    def __contains__(self, actor: object) -> bool:
        if not isinstance(actor, Actor):
            raise TypeError(f"{type(actor)} is not a Actor.")
        return actor in self.get()

    def __call__(self, *args: Breeds, **kwargs: Breeds) -> ActorsList[Actor]:
        return self.get(*args, **kwargs)

    @property
    def crs(self) -> pyproj.CRS:
        """Returns the current CRS."""
        return self._model.nature.crs

    @property
    def model(self) -> MainModel[Any, Any]:
        """The ABSESpy model where the container belongs to."""
        return self._model

    @property
    def is_full(self) -> bool:
        """Whether the container is full."""
        return (
            False
            if self._max_length is None
            else len(self.get()) >= self._max_length
        )

    @property
    def is_empty(self) -> bool:
        """Check whether the container is empty."""
        return len(self.get()) == 0

    def check_registration(
        self, actor_cls: Type[Actor], register: bool = False
    ) -> bool:
        """Whether the breed of the actor is registered.

        Parameters:
            actor_cls:
                The class of the actor.
                If the actor is registered,
                it will be accessible from all containers
                (despite count is zero).

        Returns:
            True if the breed of the actor is registered.
            False otherwise.
        """
        flag = actor_cls.breed in self.keys()
        if not flag and register:
            self._model.agents.register(actor_cls)
        return flag

    def _check_adding_for_length(self, when_adding: int = 1) -> None:
        """Check if the container is invalid for adding the agent.

        Parameters:
            when_adding:
                The number of agents to add.

        Raises:
            ABSESpyError:
                If the container is full after adding these agents.
        """
        if self._max_length is None:
            return
        if self.has() + when_adding > self._max_length:
            e1 = f"{self} is full (maximum {self._max_length}: "
            e2 = f"Now has {self.has()}), trying to add {when_adding} more."
            raise ABSESpyError(e1 + e2)

    def get(self, breeds: Breeds = None) -> ActorsList[Actor]:
        """Get all entities of specified breeds to a list.

        Parameters:
            breeds:
                The breed(s) of entities to convert to a list.
                If None, all breeds are used.

        Returns:
            ActorsList:
                A list of entities of the specified breeds.

        Example:
            ```python
            from abses import Actor, MainModel

            class Actor1(Actor):
                pass

            class Actor2(Actor):
                pass

            model = MainModel()
            model.agents.new(Actor, singleton=True)
            model.agents.new(Actor1, num=2)
            model.agents.new(Actor2, num=3)

            model.agents.get('Actor1')
            >>> '<ActorsList: (2)Actor1>'
            model.agents.get()
            >>> '<ActorsList: (1)Actor; (2)Actor1; (3)Actor2>'
            ```
        """
        # specified breeds
        breeds = self.model.breeds if breeds is None else make_list(breeds)
        # get all available agents
        agents = {
            a
            for breed, actors in self.items()
            if breed in breeds
            for a in actors
        }
        return ActorsList(self._model, objs=agents)

    def trigger(self, *args: Any, **kwargs: Any) -> Any:
        """Trigger a function for all agents in the container.

        This method calls the `trigger` method of the list of agents in the container,
        passing the same arguments and keyword arguments received by this method.

        Parameters:
            *args:
                Positional arguments to be passed to the `trigger` method of each agent.
            **kwargs:
                Keyword arguments to be passed to the `trigger` method of each agent.

        Returns:
            In row, what the triggered function returned.
        """
        return self.get().trigger(*args, **kwargs)

    def _add_one(self, agent: Actor) -> None:
        """Add one agent to the container."""
        if not self.check_registration(agent.__class__):
            raise TypeError(
                f"Breed '{agent.breed}' not registered."
                "Is it created by `agents.new()` method?"
            )
        self[agent.breed].add(agent)

    def add(
        self,
        agents: Actors,
    ) -> None:
        """Add one or more actors to the container.

        Parameters:
            agents:
                The actor(s) to add to the container.
                It can be a single actor, a list of actors, or an iterable of actors.
            register:
                Whether to register the actor(s) if they belong to a new breed.
                If any adding breed is never registered, a TypeError will be raised.
                Once a breed is registered, it will be added to all the containers globally.
                It means, it's not necessary to register the same breed again.
                Defaults to False.

        Raises:
            TypeError:
                If a breed of the actor(s) is not registered and `register` is False.
            ABSESpyError:
                If the container is full after adding these agents.
        """
        to_add = make_list(agents)
        self._check_adding_for_length(len(to_add))
        for item in to_add:
            self._add_one(item)

    def remove(self, agent: Actor) -> None:
        """Remove the given agent from the container and the schedule.
        Generally, it stores all the agents in the model.
        Therefore, it is not recommended to use this method directly.
        Consider to use `actor.die()` instead.

        Parameters:
            agent:
                The agent (actor) to remove.

        Raises:
            ABSESpyError:
                If the agent is on a cell thus cannot be removed from the global container.
        """
        if agent.on_earth:
            raise ABSESpyError(f"{agent} is still on the earth.")
        self[agent.breed].remove(agent)
        self.model.schedule.remove(agent)

    def select(self, selection: Selection) -> ActorsList:
        """Selects the actors that match the given selection criteria.
        This method calls the `select` method of the list of actors in the container,
        passing the same selection criteria received by this method.

        Parameters:
            selection:
                The selection criteria to apply.
                Either a string or a dictionary of key-value pairs.
                Each represents agent attributes to be checked against.

        Returns:
            A list of actors that match the selection criteria.

        Example:
            ```python
            from abses import Actor, MainModel

            class Actor1(Actor):
                test = 1

            class Actor2(Actor):
                test = 'testing'

            model = MainModel()
            model.agents.new(Actor, singleton=True)
            model.agents.new(Actor1, num=2)
            model.agents.new(Actor2, num=3)

            # selecting by breed.
            model.agents.select('Actor')
            >>> '<ActorsList: (1)Actor>'

            # selecting by attribute equal expression
            model.agents.select('test == 1')
            >>> '<ActorsList: (2)Actor1>'

            # selecting by key-value pairs attribute
            model.agents.select({'test': 'testing'})
            >>> '<ActorsList: (3)Actor2>'
            ```
        """
        return self.get().select(selection)

    def has(self, breeds: Breeds = None) -> int:
        """Whether the container has the breed of agents.

        Parameters:
            breeds:
                The breed(s) of agents to search.

        Returns:
            int:
                The number of agents of the specified breed(s).

        Example:
            ```python
            from abses import Actor, MainModel

            class Actor1(Actor):
                # breed 1
                pass

            class Actor2(Actor):
                # breed 2
                pass

            model = MainModel()
            model.agents.new(Actor, singleton=True)
            model.agents.new(Actor1, num=2)
            model.agents.new(Actor2, num=3)

            model.agents.has('Actor1')
            >>> 2
            model.agents.has(['Actor1', 'Actor2'])
            >>> 5
            ```
        """
        return len(self.get(breeds=breeds))

    def apply(self, func: Callable, *args: Any, **kwargs: Any) -> np.ndarray:
        """Apply a function to all agents in the container.

        Parameters:
            func:
                The function to apply to all agents in the container.
        """
        return self.get().apply(func, *args, **kwargs)

    def item(self, how: HOW = "item", index: int = 0) -> Actor | None:
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
        return self.get().item(how=how, index=index)
