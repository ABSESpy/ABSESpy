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
    from .main import MainModel

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
        _for_cell: bool = False,
    ):
        super().__init__({b: set() for b in model.breeds})
        self._model: MainModel = model
        model._containers.append(self)
        self._only_off_earth: bool = _for_cell
        self._max_length: int = max_len

    def __len__(self) -> int:
        return len(self.to_list())

    def __str__(self) -> str:
        return "<ModelAgents>"

    def __repr__(self) -> str:
        # rep = self.to_list().__repr__()[13:-1]
        strings = [f"({len(v)}){k}" for k, v in self.items()]
        return f"<ModelAgents: {'; '.join(strings)}>"

    def __getattr__(self, name: str) -> Any | Actor:
        if name[0] == "_" or name not in self.model.breeds:
            return getattr(self, name)
        return self.to_list(name)

    def __contains__(self, name) -> bool:
        return name in self.to_list()

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
            else len(self.to_list()) >= self._max_length
        )

    @property
    def is_empty(self) -> bool:
        """Whether the container is empty."""
        return len(self.to_list()) == 0

    def _check_adding_for_cell(self, agent: Actor) -> None:
        """Check if the container is invalid for adding the agent."""
        if self._only_off_earth and agent.on_earth:
            raise ABSESpyError(
                f"{agent} is on earth and cannot be added to the container."
            )

    def _check_adding_for_length(self) -> None:
        """Check if the container is invalid for adding the agent."""
        if self.is_full:
            raise ABSESpyError(
                "The container is full and cannot add more agents."
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
        self.register(breed_cls)
        objs = [breed_cls(self._model, **kwargs) for _ in range(num)]
        logger.info(f"Created {num} actors of breed {breed_cls.__name__}")
        agents = ActorsList(self._model, objs)
        self.add(agents)
        if singleton:
            return agents[0] if num == 1 else agents
        return agents

    def to_list(
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
        return self.to_list().trigger(*args, **kwargs)

    def _add_one(self, agent: Actor, register: bool = False) -> bool:
        """Add one agent to the container.

        Parameters:
            agent:
                The agent to add.

        Returns:
            If the operation is successful.
        """
        self._check_adding_for_cell(agent)
        self._check_adding_for_length()
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
        for item in make_list(agents):
            self._add_one(item, register)

    def remove(self, agent: Actor) -> None:
        """Remove the given agent from the container.

        Parameters:
            agent:
                The agent (actor) to remove.
        """
        if self._only_off_earth and agent.on_earth:
            raise ABSESpyError(
                "You should only remove the agent from the cell by 'actor.move.off()' method."
            )
        self[agent.breed].remove(agent)

    def select(self, selection: Selection) -> ActorsList:
        """Selects the actors that match the given selection criteria.

        Parameters:
            selection:
                The selection criteria to apply.

        Returns:
            A list of actors that match the selection criteria.
        """
        return self.to_list().select(selection)
