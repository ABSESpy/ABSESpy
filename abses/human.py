#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from typing import Callable, Dict, Iterator, Tuple, TypeAlias, Union

import networkx as nx
from omegaconf import DictConfig

from abses.actor import Actor

from .cells import PatchCell
from .container import AgentsContainer
from .modules import CompositeModule, Module
from .sequences import ActorsList, Selection

Actors: TypeAlias = Union[ActorsList, Selection, Actor]
Trigger: TypeAlias = Union[str, Callable]


class HumanModule(Module):
    """基本的人类模块"""

    def __init__(self, model, name=None):
        Module.__init__(self, model, name)
        self._agents = AgentsContainer(model)
        self._collections: Dict[str, Selection] = DictConfig({})
        self._rules: Dict[str, Trigger] = DictConfig({})

    def __getattr__(self, name):
        if name[0] == "_" or name not in self._collections:
            return super().__getattr__(name)
        selection = self._collections[name]
        return self.actors.select(selection)

    @property
    def agents(self) -> AgentsContainer:
        """所有的主体筛选器"""
        return self._agents

    @property
    def actors(self) -> ActorsList:
        """所有的行动者"""
        return self.agents.to_list()

    def _must_be_actor(self, actor: Actor) -> None:
        if not isinstance(actor, Actor):
            raise TypeError(
                f"Actor must be a subclass of Actor, instead of {type(actor)}."
            )

    def _must_be_cell(self, cell: PatchCell) -> None:
        if not isinstance(cell, PatchCell):
            raise TypeError(
                f"Cell must be a subclass of Cell, instead of {type(cell)}."
            )

    def define(self, name: str, selection: Selection) -> ActorsList:
        """定义一次主体查询"""
        selected = self.actors.select(selection)
        self._collections[name] = selection
        return selected

    # def rule(self, actors: Actors, when: Selection, then: Trigger, name: Optional[str] = None):
    #     if name is None:
    #         pass
    #     self.define(name=name)
    #     actors_to_trigger = actors.select(when)
    #     results = actors_to_trigger.trigger(then)
    #     return actors_to_trigger, results

    def arena(self, actor_1: Actors, actor_2: Actors, interaction: Trigger):
        """互动情景"""
        actor_1.trigger(interaction, actor_2)
        actor_2.trigger(interaction, actor_1)


class BaseHuman(CompositeModule, HumanModule):
    """基本的人类模块"""

    def __init__(self, model, name="human"):
        HumanModule.__init__(self, model, name)
        CompositeModule.__init__(self, model, name=name)
        self._bipartite_graphs: Dict[str, nx.Graph] = {}
        self._direct_graphs: Dict[str, nx.Graph] = {}
        self._links: Dict[str, bool] = {}

    @property
    def links(self) -> Tuple[str]:
        """所有关联类型"""
        return tuple(self._links.keys())

    def _add_link_between_actors(
        self,
        link: str,
        actor_1: Actor,
        actor_2: Actor,
        mutual: bool = False,
    ) -> None:
        """在两个主体之间建立关系"""
        # check type
        self._must_be_actor(actor_1)
        self._must_be_actor(actor_2)
        # links: {link, is_land}
        if self._links.get(link, False) is True:
            raise KeyError(
                f"Link '{link}' already exists but not between actors."
            )
        # add graph
        if link not in self._direct_graphs:
            self._direct_graphs[link] = nx.Graph()
        # add link
        self._direct_graphs[link].add_edge(actor_1, actor_2)
        # mutual interaction
        if mutual:
            self._direct_graphs[link].add_edge(actor_2, actor_1)

    def _add_link_between_agent_cell(
        self,
        link: str,
        agent: Actor,
        cell: PatchCell,
    ) -> None:
        self._must_be_actor(agent)
        self._must_be_cell(cell)
        # links: {link, is_land}
        if self._links.get(link, True) is False:
            raise KeyError(
                f"Link '{link}' already exists but not between actor and cell."
            )
        if link not in self._bipartite_graphs:
            graph = self._bipartite_graphs[link] = nx.Graph()
            graph.add_node(agent, bipartite=agent.breed)
            graph.add_node(cell, bipartite=cell.breed)
        self._bipartite_graphs[link].add_edge(agent, cell)

    def add_link(
        self, link: str, agent_1: Actor, agent_2: Actor | PatchCell, **kwargs
    ) -> None:
        """添加互动关系"""
        if isinstance(agent_2, Actor):
            self._add_link_between_actors(
                link=link, actor_1=agent_1, actor_2=agent_2, **kwargs
            )
            is_land = False
        elif isinstance(agent_2, PatchCell):
            self._add_link_between_agent_cell(
                link=link, agent=agent_1, cell=agent_2
            )
            is_land = True
        self._links[link] = is_land

    def get_graph(self, link: str) -> nx.Graph:
        """获取图"""
        try:
            land = self._links[link]
        except KeyError as error:
            raise KeyError(f"Link '{link}' not exists.") from error
        dic = self._bipartite_graphs if land else self._direct_graphs
        msg = "between actor and land" if land else "between actors"
        if link not in dic:
            raise KeyError(f"Link '{link}' {msg} not exists.")
        return dic[link]

    def linked(
        self,
        link: str,
        agent: Actor,
    ) -> Iterator[Actor]:
        """获取相关联的所有其它主体"""
        graph = self.get_graph(link)
        if isinstance(graph, nx.DiGraph):
            return graph.successors(agent)
        return nx.all_neighbors(graph=graph, node=agent)
