#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Dict,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    Type,
)

import networkx as nx

if TYPE_CHECKING:
    from abses.human import BaseHuman


class LinkContainer:
    """连接容器"""

    def __init__(self) -> None:
        self._bipartite: Dict[str, bool] = {}
        self._graphs: Dict[str, nx.Graph] = {}

    @property
    def links(self) -> Tuple[str]:
        """所有关联类型"""
        return tuple(self._graphs.keys())

    def _is_bipartite(self, node_1, node_2) -> bool:
        """是否是二分图"""
        return type(node_1) is not type(node_2)

    def _is_new_links_graph(self, link: str) -> bool:
        """是否是新的图"""
        return link not in self.links

    def _is_node(self, node: LinkNode, check: bool = True) -> bool:
        """是否是节点"""
        flag = isinstance(node, LinkNode)
        if check and not flag:
            raise TypeError(f"{node} is not a LinkNode.")
        return flag

    def _add_new_graph(
        self, link: str, graph_cls: Type, is_bipartite: bool
    ) -> None:
        """添加新图"""
        if not issubclass(graph_cls, nx.Graph):
            raise TypeError(
                f"Initializing a new link type '{link}', you must assign a valid graph type, instead of {graph_cls}."
            )
        self._bipartite[link] = is_bipartite
        self._graphs[link] = graph_cls()

    def _is_directed_graph(self, graph: Type | str) -> bool:
        if isinstance(graph, str):
            if self._is_new_links_graph(graph):
                raise KeyError(f"Link {graph} does not exist.")
            graph = type(self._graphs[graph])
            return self._is_directed_graph(graph)
        return graph in (nx.MultiDiGraph, nx.DiGraph)

    def add_link(
        self,
        node_1,
        node_2,
        link: str,
        graph_cls: Type = None,
        mutual: Optional[bool] = None,
    ) -> bool:
        """添加关联"""
        self._is_node(node_1, check=True)
        self._is_node(node_2, check=True)
        if self._is_new_links_graph(link):
            is_bipartite = self._is_bipartite(node_1, node_2)
            self._add_new_graph(link, graph_cls, is_bipartite)
        if self._is_directed_graph(graph_cls) and mutual is None:
            raise TypeError(
                f"{graph_cls} is Directed Graph, mutual must be set."
            )
        self.linking(node_1, node_2, link, mutual=mutual)

    def linking(
        self,
        node_1: LinkNode,
        node_2: LinkNode,
        link: str,
        mutual: bool = True,
    ) -> None:
        """建立关联"""
        graph = self.get_graph(link)
        if self._bipartite[link]:
            graph.add_node(node_1, bipartite=node_1.breed)
            graph.add_node(node_2, bipartite=node_2.breed)
        node_1.links.add(link)
        node_2.links.add(link)
        graph.add_edge(node_1, node_2)
        if mutual:
            graph.add_edge(node_2, node_1)

    def get_graph(self, link: str) -> nx.Graph:
        """获取图"""
        if self._is_new_links_graph(link=link):
            raise KeyError(f"Link {link} does not exist.")
        return self._graphs[link]

    def linked(
        self,
        link: str,
        node: LinkNode,
    ) -> Iterator[LinkNode]:
        """获取相关联的所有其它主体"""
        graph = self.get_graph(link)
        if isinstance(graph, nx.DiGraph):
            return graph.successors(node)
        return nx.all_neighbors(graph=graph, node=node)


class LinkNode:
    """节点类"""

    def __init__(self) -> None:
        self._container: LinkContainer = None
        self._links: Set[str] = set()

    @classmethod
    @property
    def breed(cls) -> str:
        """种类"""
        return cls.__name__

    @property
    def links(self) -> List[str]:
        """该主体所有连接类型"""
        return self._links

    @property
    def container(self) -> LinkContainer:
        """连接容器"""
        return self._container

    @container.setter
    def container(self, container: LinkContainer) -> None:
        if not isinstance(container, LinkContainer):
            raise TypeError(f"{container} is not a LinkContainer.")
        self._container = container

    def link_to(
        self,
        agent: LinkNode,
        link: Optional[str],
        graph_cls: Type = nx.Graph,
        **kwargs,
    ) -> None:
        """将行动者与其它行动者或地块建立连接"""
        self.container.add_link(
            node_1=self, node_2=agent, link=link, graph_cls=graph_cls, **kwargs
        )

    def linked(self, link: str) -> Iterator[LinkNode]:
        """获取相关联的所有其它主体，如果不在连接容器中，则返回空列表"""
        return (
            iter([])
            if link not in self.links
            else self.container.linked(link, self)
        )
