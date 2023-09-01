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

from agentpy import AttrDict

from abses.actor import Actor
from abses.sequences import ActorsList, Selection
from abses.tools.func import make_list

if TYPE_CHECKING:
    from .main import MainModel

logger = logging.getLogger("__name__")


class AgentsContainer(AttrDict):
    """Singleton AgentsContainer for each model."""

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
            return super().__getattr__(name)
        else:
            return self.to_list(name)

    def __contains__(self, name):
        return name in self.to_list()

    @property
    def breeds(self):
        """多少种主体种类"""
        return tuple(self._breeds.keys())

    @property
    def model(self):
        """对应的模型"""
        return self._model

    def _register(self, actor: Actor) -> None:
        if actor.breed not in self._breeds:
            self._breeds[actor.breed] = type(actor)
            self[actor.breed] = set()

    def create(
        self, breed_cls: Type[Actor], num: int = 1, singleton: bool = False
    ) -> Union[Actor, ActorsList]:
        """创建某类主体"""
        agents = ActorsList(self._model, objs=num, cls=breed_cls)
        self.add(agents, register=True)
        if singleton:
            return agents[0] if num == 1 else agents
        return agents

    # def create_from(self, breeds: dict):
    #     for breed_cls, n in breeds.items():
    #         self.create_agents(breed_cls, n)

    def to_list(
        self, breeds: Optional[Union[str, Iterable[str]]] = None
    ) -> ActorsList:
        """将所有种类的主体转换为列表"""
        if breeds is None:
            breeds = self.breeds
        agents = ActorsList(self._model)
        for breed in make_list(breeds):
            agents.extend(self[breed])
        return agents

    def add(
        self,
        agents: Union[Actor, ActorsList, Iterable[Actor]] = None,
        register: bool = False,
    ) -> None:
        """添加主体"""
        dic = ActorsList(self._model, make_list(agents)).to_dict()
        for k, actors_lst in dic.items():
            if k not in self.breeds:
                if register:
                    self._register(actors_lst[0])
                else:
                    raise TypeError(f"'{k}' not registered.")
            self[k] = self[k].union(actors_lst)

    def remove(self, agent: Actor) -> None:
        """移除特定 Agent"""
        self[agent.breed].remove(agent)
        if agent.on_earth:
            self._model.nature.remove(agent)

    def select(self, selection: Selection) -> ActorsList:
        """选择主体"""
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
