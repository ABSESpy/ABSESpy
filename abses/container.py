#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

import threading
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    Optional,
    Self,
    Tuple,
    Type,
    Union,
)

from loguru import logger

from abses.actor import Actor
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

    def __init__(self, model: MainModel):
        super().__init__()
        self._model = model
        self._breeds = {}

    def __len__(self):
        return len(self.to_list())

    def __repr__(self):
        # "<ActorsList: >"
        rep = self.to_list().__repr__()[13:-1]
        return f"<AgentsContainer: {rep}>"

    def __getattr__(self, name: str) -> Any:
        if name[0] == "_" or name not in self._breeds:
            return getattr(self, name)
        return self.to_list(name)

    def __contains__(self, name):
        return name in self.to_list()

    @property
    def breeds(self) -> Tuple[str]:
        """Get all breeds in the model"""
        return tuple(self._breeds.keys())

    @property
    def model(self) -> MainModel:
        """The ABSESpy model where the container belongs to."""
        return self._model

    def _register(self, actor: Actor) -> None:
        if actor.breed not in self._breeds:
            self._breeds[actor.breed] = type(actor)
            self[actor.breed] = set()

    def register_a_breed(self, actor_cls: type[Actor]) -> None:
        """Register a new breed of actors in the container.

        Parameters:
            actor_cls:
                The class of the actor to be registered.

        Raises:
            TypeError:
                If the given class is not a subclass of `Actor`.
        """
        if not issubclass(actor_cls, Actor):
            raise TypeError(f"'{actor_cls}' not subclass of 'Actor'.")
        self._breeds[actor_cls.breed] = actor_cls
        self[actor_cls.breed] = set()

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
        objs = [breed_cls(self._model, **kwargs) for _ in range(num)]
        logger.info(f"Created {num} actors of breed {breed_cls.__name__}")
        agents = ActorsList(self._model, objs)
        self.add(agents, register=True)
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
        if breeds is None:
            breeds = self.breeds
        agents = ActorsList(self._model)
        for breed in make_list(breeds):
            agents.extend(self[breed])
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
        dic = ActorsList(self._model, make_list(agents)).to_dict()
        for k, actors_lst in dic.items():
            if k not in self.breeds:
                if register:
                    self._register(actors_lst[0])
                else:
                    raise TypeError(f"'{k}' not registered.")
            self[k] = self[k].union(actors_lst)

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
        return self.to_list().select(selection)
