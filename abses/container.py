#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
行动者容器，集中保存行动者。
Container for actors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable, Type, Union

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

from loguru import logger

from abses.actor import Actor, Breeds
from abses.errors import ABSESpyError
from abses.sequences import ActorsList, Selection
from abses.tools.func import make_list

if TYPE_CHECKING:
    from abses.cells import PatchCell
    from abses.main import MainModel

ActorTypes: TypeAlias = Union[Type[Actor], Iterable[Type[Actor]]]
Actors: TypeAlias = Union[Actor, ActorsList, Iterable[Actor]]


class _AgentsContainer(dict):
    """AgentsContainer for the main model."""

    def __init__(
        self,
        model: MainModel,
        max_len: None | int = None,
    ):
        super().__init__({b: set() for b in model.breeds})
        self._model: MainModel = model
        model._containers.append(self)
        self._max_length: int = max_len

    def __len__(self) -> int:
        return len(self.get())

    def __str__(self) -> str:
        return "ModelAgents"

    def __repr__(self) -> str:
        strings = [f"({len(v)}){k}" for k, v in self.items()]
        return f"<{str(self)}: {'; '.join(strings)}>"

    def __contains__(self, name) -> bool:
        return name in self.get()

    def __call__(self, *args, **kwargs) -> ActorsList[Actor]:
        return self.get(*args, **kwargs)

    @property
    def model(self) -> MainModel:
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

    def check_registration(self, actor_cls: Type[Actor]) -> bool:
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
        return actor_cls.breed in self.keys()

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

    def register(self, actor_cls: ActorTypes) -> None:
        """Registers a new breed of actors.

        Parameters:
            actor_cls:
                The class of the actor to register.
                It can be a single class, or an iterable of classes.
                Once a breed is registered,
                it will be added to all the containers of the model globally.
                It means, it's not necessary to register the same breed again.

        Raises:
            ValueError:
                If the breed is already registered.
        """
        for a_cls in make_list(actor_cls):
            breed = a_cls.breed
            if breed in self._model.breeds:
                raise ValueError(f"{breed} is already registered.")
            self._model.breeds = a_cls

    def new(
        self,
        breed_cls: Type[Actor],
        num: int = 1,
        singleton: bool = False,
        **kwargs: dict[str, Any],
    ) -> Union[Actor, ActorsList[Actor]]:
        """Create one or more actors of the given breed class.

        Parameters:
            breed_cls:
                The breed class of the actor(s) to create.
            num:
                The number of actors to create. Defaults to 1.
            singleton (bool, optional):
                Whether to create a singleton actor. Defaults to False.
            **kwargs:
                Additional keyword arguments to pass to the actor constructor.

        Returns:
            The created actor(s).

        Example:
            ```python
            from abses import Actor, MainModel
            model = MainModel()
            actor = model.agents.new(singleton=True)
            >>> type(actor)
            >>> Actor

            actors = model.agents.new(singleton=False)
            >>> type(actors)
            >>> ActorsList
            ```
        """
        # check if the breed class is registered, if not, register it.
        if not self.check_registration(breed_cls):
            self.register(breed_cls)
        # create actors.
        objs = [breed_cls(self._model, **kwargs) for _ in range(num)]
        logger.info(f"Created {num} actors of breed {breed_cls.__name__}")
        # add actors to the container and the schedule.
        for agent in objs:
            self.add(agent)
            self.model.schedule.add(agent)
        # return the created actor(s).
        if singleton:
            return objs[0] if num == 1 else objs
        return ActorsList(model=self.model, objs=objs)

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

    def _add_one(self, agent: Actor, register: bool = False) -> None:
        """Add one agent to the container."""
        if agent.breed not in self.keys():
            if register:
                self.register(agent.__class__)
            else:
                raise TypeError(
                    f"'{agent.breed}' not registered. Is it created by `.create()` method?"
                )
        self[agent.breed].add(agent)

    def add(
        self,
        agents: Actors,
        register: bool = False,
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
            self._add_one(item, register)

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

    def apply(self, func: callable, *args, **kwargs) -> None:
        """Apply a function to all agents in the container.

        Parameters:
            func:
                The function to apply to all agents in the container.
        """
        return self.get().apply(func, *args, **kwargs)


class _CellAgentsContainer(_AgentsContainer):
    """Container for agents located at cells."""

    def __init__(
        self, model: MainModel, cell: PatchCell, max_len: int | None = None
    ):
        super().__init__(model, max_len)
        self._cell = cell

    def __str__(self) -> str:
        return "CellAgents"

    def _add_one(
        self, agent: Actor, register: TYPE_CHECKING = False
    ) -> TYPE_CHECKING:
        if agent.on_earth and agent not in self:
            e1 = f"{agent} is on another cell thus cannot be added."
            e2 = "You may use 'actor.move.to()' to change its location."
            e3 = "Or you may use 'actor.move.off()' before adding it."
            raise ABSESpyError(e1 + e2 + e3)
        super()._add_one(agent, register)
        agent.at = self._cell

    def remove(self, agent: Actor) -> None:
        """Remove the given agent from the cell.
        Generally, it stores all the agents on this cell.
        Therefore, it is not recommended to use this method directly.
        Consider to use `actor.move.off()` to let the actor leave this cell instead.

        Parameters:
            agent:
                The agent (actor) to remove.

        Raises:
            ABSESpyError:
                If the agent is not on this cell.
        """
        if agent.at is not self._cell:
            raise ABSESpyError(f"{agent} is not on this cell.")
        self[agent.breed].remove(agent)
        del agent.at

    def new(
        self,
        breed_cls: Actor,
        num: int = 1,
        singleton: TYPE_CHECKING = False,
        **kwargs: Any,
    ) -> Actor | ActorsList:
        """Creates a new actor or a list of actors of the given breed class.
        The created actors are added to both the cell and the model's global container.

        Parameters:
            breed_cls:
                The breed class of the actor(s) to create.
            num:
                The number of actors to create. Defaults to 1.
            singleton:
                Whether to create a singleton actor. Defaults to False.
            **kwargs:
                Additional keyword arguments to pass to the actor constructor.

        Returns:
            The created actor(s).
        """
        # create a list of actors
        new_actors = super().new(breed_cls, num, singleton, **kwargs)
        # also add the actors to the model's global agents container
        self.model.agents.add(new_actors)
        # move the actors to the cell
        for a in make_list(new_actors):
            a.move.to(self._cell)
        return new_actors
