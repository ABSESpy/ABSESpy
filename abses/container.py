#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable, Optional, Type, Union

from loguru import logger

from abses.actor import Actor
from abses.errors import ABSESpyError
from abses.sequences import ActorsList, Selection
from abses.tools.func import make_list

if TYPE_CHECKING:
    from abses.cells import PatchCell
    from abses.main import MainModel

# logger = logging.getLogger("__name__")


class _AgentsContainer(dict):
    """Singleton AgentsContainer for each model.

    This class is a dictionary-like container for managing agents in a simulation model. It is designed to be a singleton,
    meaning that there is only one instance of this class per model. It provides methods for creating, adding, removing,
    and selecting agents, as well as triggering events.
    """

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
        # rep = self.to_list().__repr__()[13:-1]
        strings = [f"({len(v)}){k}" for k, v in self.items()]
        return f"<{str(self)}: {'; '.join(strings)}>"

    def __getattr__(self, name: str) -> Any | Actor:
        return (
            self.get(name)
            if name in self.model.breeds
            else getattr(self, name)
        )

    def __contains__(self, name) -> bool:
        return name in self.get()

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
        """Whether the container is empty."""
        return len(self.get()) == 0

    def check_registration(self, actor_cls: Type[Actor]) -> bool:
        """Whether the breed of the actor is registered."""
        return actor_cls.breed in self.keys()

    def _check_adding_for_length(self, when_adding: int = 1) -> None:
        """Check if the container is invalid for adding the agent."""
        if self._max_length is None:
            return
        now = len(self.get())
        if now + when_adding > self._max_length:
            raise ABSESpyError(
                f"{self} is full (maximum {self._max_length}: Now has {now}), trying to add {when_adding} more."
            )

    def register(self, actor_cls: Type[Actor] | Iterable[Type[Actor]]) -> None:
        """Registers a new breed of actors."""
        for a_cls in make_list(actor_cls):
            breed = a_cls.breed
            if breed in self._model.breeds:
                raise ValueError(f"{breed} is already registered.")
            self._model.breeds = a_cls

    def create(
        self,
        breed_cls: Type[Actor],
        num: int = 1,
        singleton: bool = False,
        **kwargs,
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
            actor = model.agents.create(singleton=True)
            >>> type(actor)
            >>> Actor

            actors = model.agents.create(singleton=False)
            >>> type(actors)
            >>> ActorsList
            ```
        """
        if not self.check_registration(breed_cls):
            self.register(breed_cls)
        objs = [breed_cls(self._model, **kwargs) for _ in range(num)]
        logger.info(f"Created {num} actors of breed {breed_cls.__name__}")
        agents = ActorsList(self._model, objs)
        self.add(agents)
        if singleton:
            return agents[0] if num == 1 else agents
        return agents

    def get(
        self, breeds: Optional[Union[str, Iterable[str]]] = None
    ) -> ActorsList[Actor]:
        """Get all entities of specified breeds to a list.

        Parameters:
            breeds:
                The breed(s) of entities to convert to a list (Optional[Union[str, Iterable[str]]]). If None, all breeds are used.

        Returns:
            ActorsList:
                A list of entities of the specified breeds.
        """
        breeds = self.model.breeds if breeds is None else make_list(breeds)
        agents = ActorsList(self._model)
        for k, values in self.items():
            if k in breeds:
                agents.extend(values)
        return agents

    def trigger(self, *args, **kwargs) -> Any:
        """Trigger a function for all agents in the container.

        This method calls the `trigger` method of the list of agents in the container,
        passing the same arguments and keyword arguments received by this method.

        Parameters:
            *args:
                Positional arguments to be passed to the `trigger` method of each agent.
            **kwargs:
                Keyword arguments to be passed to the `trigger` method of each agent.

        Returns:
            None
        """
        return self.get().trigger(*args, **kwargs)

    def _add_one(self, agent: Actor, register: bool = False) -> bool:
        """Add one agent to the container.

        Parameters:
            agent:
                The agent to add.

        Returns:
            If the operation is successful.
        """
        if agent.breed not in self.keys():
            if register:
                self.register(agent.__class__)
            else:
                raise TypeError(
                    f"'{agent.breed}' not registered. Is it created by `.create()` method?"
                )
        self[agent.breed].add(agent)
        return True

    def add(
        self,
        agents: Union[Actor, ActorsList, Iterable[Actor]] = None,
        register: bool = False,
    ) -> None:
        """Add one or more actors to the container.

        Parameters:
            agents:
                The actor(s) to add to the container. Defaults to None.
            register:
                Whether to register the actor(s) if they belong to a new breed. Defaults to False.

        Raises:
            TypeError:
                If a breed of the actor(s) is not registered and `register` is False.
        """
        to_add = make_list(agents)
        self._check_adding_for_length(len(to_add))
        for item in to_add:
            self._add_one(item, register)

    def remove(self, agent: Actor) -> None:
        """Remove the given agent from the container.

        Parameters:
            agent:
                The agent (actor) to remove.
        """
        self[agent.breed].remove(agent)

    def select(self, selection: Selection) -> ActorsList:
        """Selects the actors that match the given selection criteria.

        Parameters:
            selection:
                The selection criteria to apply.

        Returns:
            A list of actors that match the selection criteria.
        """
        return self.get().select(selection)


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
            raise ABSESpyError(
                f"{agent} is on another cell thus cannot be added. You may use 'actor.move.to()' to change its location. Or you may use 'actor.move.off()' before adding it."
            )
        super()._add_one(agent, register)
        agent.at = self._cell

    def remove(self, agent: Actor) -> None:
        """Remove the given agent from the container."""
        super().remove(agent)
        del agent.at

    def create(
        self,
        breed_cls: Actor,
        num: int = 1,
        singleton: TYPE_CHECKING = False,
        **kwargs,
    ) -> Actor | ActorsList:
        new_actors = super().create(breed_cls, num, singleton, **kwargs)
        self.model.agents.add(new_actors)
        for a in make_list(new_actors):
            a.move.to(self._cell)
        return new_actors
