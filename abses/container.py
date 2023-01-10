#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import logging
from collections import UserDict
from collections.abc import Iterable
from numbers import Number
from typing import List, Optional

import numpy as np
from agentpy import Agent, AgentList

from .objects import BaseAgent
from .tools.func import make_list, norm_choice

logger = logging.getLogger("__name__")


class BaseAgentList(AgentList):
    def __repr__(self):
        return f"<List: {self.__len__()} {self.breed()}s>"

    def breed(self):
        breeds = np.unique([p.breed for p in self])
        breed = self._check_breed(breeds)
        return breed

    def _check_length(self, length):
        if not hasattr(self, "__len__"):
            raise ValueError(f"{type(length)} object is not iterable.")
        if not length.__len__() == self.__len__():
            raise ValueError(
                f"{type(length)} length is {len(length)}, mismatch with {self}."
            )

    def _check_breed(self, breeds):
        if len(breeds) == 0:
            return None
        elif len(breeds) > 1:
            logger.warning(f"Creating AgentsList with mixed breeds: {breeds}.")
        else:
            return breeds[0]

    def select(self, selection: Iterable[bool]) -> List[BaseAgent]:
        """Returns a new :class:`BaseAgentList` based on `selection`.

        Arguments:
            selection (list of bool): List with same length as the agent list.
                Positions that return True will be selected.
        """
        self._check_length(selection)
        return BaseAgentList(
            self.model, [a for a, s in zip(self, selection) if s]
        )

    def ids(self, ids: Iterable[int]) -> List[BaseAgent]:
        """
        Select by a `ids` list of Agent.

        Args:
            ids (iterable): an iterable id list. List[id], ID is an attr of agent obj.

        Returns:
            BaseAgentList: A subset of origin agents list.
        """
        ids = make_list(ids)
        agents = self.select([agent.id in ids for agent in self])
        return agents

    def random_choose(
        self, p=None, size: int = 1, replace: bool = False
    ) -> BaseAgent:
        if size == 1:
            return norm_choice(self, p=p)
        elif size > 1:
            chosen = norm_choice(self, p=p, size=size)
            return BaseAgentList(self.model, chosen)

    def better(
        self, metric, than: "Number|BaseAgent|None" = None
    ) -> AgentList:
        metrics = self.metrics.get(metric)
        if than is None:
            return self.select(metrics == max(metrics))
        elif isinstance(than, Number):
            return self.select(metrics > than)
        elif isinstance(than, BaseAgent):
            diff = self.diff(metric, than)
            return self.select(diff > 0)

    def diff(self, metric: str, other) -> np.ndarray:
        diff = self.metrics.get(metric) - other.metrics.get(metric)
        return np.array(diff)

    def update(self, attr: str, values: Iterable[any]) -> None:
        [agent.update(attr, val) for agent, val in zip(self, values)]

    def decision_is(self, decision, rate=False):
        selected = self.select(self.decision.now == decision)
        if rate:
            return len(selected) / len(self)
        else:
            return selected

    def split(self, where: Iterable[int]) -> np.ndarray:
        """
        split agents into N+1 groups.

        Args:
            where (Iterable[int]): indexes [size=N] denotes where to split.

        Returns:
            np.ndarray: N+1 groups: agents array
        """
        to_split = np.array(self)
        return np.hsplit(to_split, where)

    def remove(self, agents: Iterable[Agent]) -> None:
        for agent in make_list(agents):
            super().remove(agent)

    def array(
        self, attr: str, how: "int|str" = "attr", *args, **kwargs
    ) -> np.ndarray:
        if how == "attr":
            results = getattr(self, attr)
        elif isinstance(how, int):
            results = self.decision.get(how)
        elif how == "metric":
            results = self.metrics.get(attr)
        elif how == "loc":
            results = self.loc(attr)
        elif how == "mine":
            results = self.mine(attr, *args, **kwargs)
        return np.array(results)

    def position_to_coord(self, x_coords, y_coords):
        X, Y = np.meshgrid(x_coords, y_coords)
        lon = [X[x, y] for x, y in self.pos]
        lat = [Y[x, y] for x, y in self.pos]
        return lon, lat


class AgentsContainer(UserDict):
    def __init__(self, model, agents: AgentList = None):
        super().__init__()
        self._model = model
        self._breeds = {}
        self.add(agents)

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
        self.__setattr__(name, self[name])
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

    def now(self, breed: Optional[str] = None) -> BaseAgentList:
        if breed is None:
            agents = self.to_list()
        else:
            agents = self[breed]
        return agents.select(agents.on_earth)

    def to_list(self) -> BaseAgentList:
        agents = BaseAgentList(self._model)
        for _, agents_lst in self.items():
            agents.extend(agents_lst)
        return agents

    def _verify_agent(self, agent):
        if not isinstance(agent, (BaseAgent, Agent)):
            return None
        else:
            breed = agent.__class__.__name__.lower()
            if breed not in self.breeds:
                self[breed] = BaseAgentList(model=self._model)
                self.breeds = agent.__class__
            return breed

    def add(self, agents: AgentList = None) -> None:
        agents = make_list(agents)
        for agent in agents:
            breed = self._verify_agent(agent)
            if breed is None:
                continue
            else:
                self[breed].append(agent)

    def get_breed(self, breed: str) -> BaseAgentList:
        if breed in self.breeds:
            return self[breed]
        else:
            return BaseAgentList(model=self._model)

    def remove(self, agents: BaseAgentList = None) -> None:
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
        manipulate_agents_func (warped function): should be a method of module.
    """

    def apply(self, agents=None, *args, **kwargs):
        if agents is None:
            agents = self.model.agents
            results = agents.apply(func, sender=self, *args, **kwargs)
        else:
            results = func(self, agents=agents, *args, **kwargs)
        return results

    return apply
