#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import networkx as nx

from .container import AgentsContainer, BaseAgentList
from .modules import CompositeModule


class BaseHuman(CompositeModule):
    def __init__(self, model, name="human"):
        CompositeModule.__init__(self, model, name=name)
        self.arguments = ["agents"]

    def create_agents(self, breed_cls, n):
        name = f"{breed_cls.__name__.lower()}"
        agents = BaseAgentList(self.model, objs=n, cls=breed_cls)
        self._set_agents(name, agents)
        self._set_graph(name, agents)
        return agents

    def create_agents_from(self, breeds: dict) -> AgentsContainer:
        """
        Generate agents.

        Args:
            breeds (dict): {Agent class: number to create}

        Returns:
            AgentsContainer: model's agents container.
        """
        for breed_cls, n in breeds.items():
            self.create_agents(breed_cls, n)

    def _set_graph(
        self, name, agents: BaseAgentList, graph: nx.Graph = None, **kwargs
    ) -> None:
        if graph is None:
            graph = nx.Graph(**kwargs)
            self.logger.info(f"Generate graph for breed: '{name}'.")
        graph.add_nodes_from(agents)
        setattr(self, f"{name}s_graph", graph)

    def _set_agents(self, name, agents):
        self.agents = agents
        self.__setattr__(f"{name}s", self.agents[name])
        self.inheritance = f"{name}s"
        self.logger.info(f"Create {len(agents)} {name}s.")
        self.notify()

    def require(self, attr: str) -> object:
        return self.mediator.transfer_require(self, attr)

    pass
