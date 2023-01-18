#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import logging
from typing import Optional

from agentpy import Agent, AttrDict

from .actor import Actor
from .sequences import ActorsList
from .tools.func import make_list, norm_choice

logger = logging.getLogger("__name__")


class AgentsContainer(AttrDict):
    def __init__(self, model):
        super().__init__()
        self._model = model
        self._breeds = {}

    def __len__(self):
        return len(self.to_list())

    def __repr__(self):
        return f"<AgentsContainer: {[f'{breed}: {len(agents)}' for breed, agents in self.items()]}>"

    @property
    def breeds(self):
        return tuple(self._breeds.keys())

    @breeds.setter
    def breeds(self, breed_cls):
        name = breed_cls.__name__.lower()
        self._breeds[name] = breed_cls

    def apply(
        self, func: callable, sender: object = None, *args, **kwargs
    ) -> dict:
        results = {}
        for breed, agents in self.items():
            if sender:
                res = func(sender, agents, *args, **kwargs)
            else:
                res = func(agents, *args, **kwargs)
            results[breed] = res
        return results

    def now(self, breed: Optional[str] = None) -> ActorsList:
        if breed is None:
            agents = self.to_list()
        else:
            agents = self[breed]
        return agents.select(agents.on_earth)

    def to_list(self) -> ActorsList:
        agents = ActorsList(self._model)
        for _, agents_lst in self.items():
            agents.extend(agents_lst)
        return agents

    def _verify_agent(self, agent):
        if not isinstance(agent, (Actor, Agent)):
            return None
        else:
            breed = agent.__class__.__name__.lower()
            if breed not in self.breeds:
                self[breed] = ActorsList(model=self._model)
                self.breeds = agent.__class__
            return breed

    def add(self, agents: ActorsList = None) -> None:
        agents = make_list(agents)
        for agent in agents:
            breed = self._verify_agent(agent)
            if breed is None:
                continue
            else:
                self[breed].append(agent)

    def get_breed(self, breed: str) -> ActorsList:
        if breed in self.breeds:
            return self[breed]
        else:
            return ActorsList(model=self._model)

    def remove(self, agents: ActorsList = None) -> None:
        for agent in make_list(agents):
            breed = self._verify_agent(agent)
            self[breed].remove(agent)
            del agent
            if len(self[breed]) == 0:
                del self[breed]


def apply_agents(func) -> callable:
    """
    Apply this method to all agents of model if input agents argument is None.

    Args:
        manipulate_agents_func (wrapped function): should be a method of module.
    """

    def apply(self, agents=None, *args, **kwargs):
        if agents is None:
            agents = self.model.agents
            results = agents.apply(func, sender=self, *args, **kwargs)
        else:
            results = func(self, agents=agents, *args, **kwargs)
        return results

    return apply
