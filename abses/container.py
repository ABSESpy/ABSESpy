#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

import logging
import threading
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    Optional,
    Self,
    Type,
    Union,
)

from abses.actor import Actor
from abses.sequences import ActorsList, Selection
from abses.tools.func import make_list

if TYPE_CHECKING:
    from .main import MainModel

logger = logging.getLogger("__name__")


class AgentsContainer(dict):
    """
    Singleton AgentsContainer for each model.

    This class is a dictionary-like container for managing agents in a simulation model. It is designed to be a singleton,
    meaning that there is only one instance of this class per model. It provides methods for creating, adding, removing,
    and selecting agents, as well as triggering events.

    Attributes
    ----------
    _models : Dict[MainModel, AgentsContainer]
        A dictionary that maps each model to its corresponding AgentsContainer
        instance.
    _lock : threading.RLock
        A reentrant lock that is used to synchronize access to the _models dictionary.

    Parameters
    ----------
    model : MainModel
        The main model that this AgentsContainer belongs to.

    Properties
    ----------
    breeds : Tuple[str]
        A tuple of all the breeds (types) of agents that are registered in this container.
    model : MainModel
        The main model that this AgentsContainer belongs to.

    Methods:
    register_a_breed(actor_cls: Type[Actor]) -> None
        Registers a new breed (type) of agent in this container.
    create(breed_cls: Type[Actor], num: int = 1, singleton: bool = False, **kwargs) -> Union[Actor, ActorsList]
        Creates a specified number of agents of a specified breed (type) and adds them to this container.
    to_list(breeds: Optional[Union[str, Iterable[str]]] = None) -> ActorsList
        Returns a list of all agents in this container, or a list of agents of specified breeds (types).
    trigger(*args, **kwargs) -> None
        Triggers an event for all agents in this container.
    add(agents: Union[Actor, ActorsList, Iterable[Actor]] = None, register: bool = False) -> None
        Adds one or more agents to this container.
    remove(agent: Actor) -> None
        Removes a specified agent from this container.
    select(selection: Selection) -> ActorsList
        Selects a subset of agents from this container based on a specified selection criteria.
    """

    _models: Dict[MainModel, AgentsContainer] = {}
    _lock = threading.RLock()

    def __new__(cls: type[Self], model: MainModel) -> Self:
        instance = cls._models.get(model)
        if instance is None:
            instance = super().__new__(cls)
            with cls._lock:
                cls._models[model] = instance
        return instance

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
    def breeds(self):
        """Get all breeds in the model"""
        return tuple(self._breeds.keys())

    @property
    def model(self):
        """Get main model."""
        return self._model

    def _register(self, actor: Actor) -> None:
        if actor.breed not in self._breeds:
            self._breeds[actor.breed] = type(actor)
            self[actor.breed] = set()

    def register_a_breed(self, actor_cls: type[Actor]) -> None:
        """
        Register a new breed of actors in the container.

        Args:
            actor_cls (type[Actor]): The class of the actor to be registered.

        Raises:
            TypeError: If the given class is not a subclass of `Actor`.

        Returns:
            None
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
    ) -> Union[Actor, ActorsList]:
        """
        Create one or more actors of the given breed class.

        Args:
            breed_cls (Type[Actor]): The breed class of the actor(s) to create.
            num (int, optional): The number of actors to create. Defaults to 1.
            singleton (bool, optional): Whether to create a singleton actor. Defaults to False.
            **kwargs: Additional keyword arguments to pass to the actor constructor.

        Returns:
            Union[Actor, ActorsList]: The created actor(s).
        """
        objs = [breed_cls(self._model, **kwargs) for _ in range(num)]
        agents = ActorsList(self._model, objs)
        self.add(agents, register=True)
        if singleton:
            return agents[0] if num == 1 else agents
        return agents

    def to_list(
        self, breeds: Optional[Union[str, Iterable[str]]] = None
    ) -> ActorsList:
        """
        Get all entities of specified breeds to a list.

        Args:
            breeds (Optional[Union[str, Iterable[str]]]): The breed(s) of entities to convert to a list. If None, all breeds are used.

        Returns:
            ActorsList: A list of entities of the specified breeds.
        """
        if breeds is None:
            breeds = self.breeds
        agents = ActorsList(self._model)
        for breed in make_list(breeds):
            agents.extend(self[breed])
        return agents

    def trigger(self, *args, **kwargs) -> None:
        """
        Trigger a function for all agents in the container.

        This method calls the `trigger` method of the list of agents in the container,
        passing the same arguments and keyword arguments received by this method.

        Args:
            *args: Positional arguments to be passed to the `trigger` method of each agent.
            **kwargs: Keyword arguments to be passed to the `trigger` method of each agent.

        Returns:
            None
        """
        return self.to_list().trigger(*args, **kwargs)

    def add(
        self,
        agents: Union[Actor, ActorsList, Iterable[Actor]] = None,
        register: bool = False,
    ) -> None:
        """
        Add one or more actors to the container.

        Args:
            agents (Union[Actor, ActorsList, Iterable[Actor]], optional): The actor(s) to add to the container. Defaults to None.
            register (bool, optional): Whether to register the actor(s) if they belong to a new breed. Defaults to False.

        Raises:
            TypeError: If a breed of the actor(s) is not registered and `register` is False.

        Returns:
            None
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
        """
        Remove the given agent from the container.

        Args:
            agent (Actor): The agent to remove.

        Returns:
            None
        """
        self[agent.breed].remove(agent)

    def select(self, selection: Selection) -> ActorsList:
        """
        Selects the actors that match the given selection criteria.

        Args:
            selection (Selection): The selection criteria to apply.

        Returns:
            ActorsList: A list of actors that match the selection criteria.
        """
        return self.to_list().select(selection)


def apply_agents(func) -> callable:
    """
    Apply this method to all agents of model if input agents argument is None.

    Args:
        manipulate_agents_func (wrapped function): should be a method of module.
    """

    def apply(self, *args, agents=None, **kwargs):
        if agents is None:
            agents = self.model.agents
            results = agents.apply(func, sender=self, *args, **kwargs)
        else:
            results = func(self, agents=agents, *args, **kwargs)
        return results

    return apply
