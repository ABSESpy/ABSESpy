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
    Iterable,
    List,
    Optional,
    Set,
    TypeAlias,
)

from abses.sequences import ActorsList

# from abses.objects import _LinkNode

if TYPE_CHECKING:
    from abses import MainModel
    from abses.actor import Actor
    from abses.cells import PatchCell

Node: TypeAlias = "Actor | PatchCell"


class _LinkContainer:
    """Container for links."""

    def __init__(self) -> None:
        self._back_links: Dict[str, Dict[int, Set]] = {}
        self._links: Dict[str, Dict[int, Set]] = {}
        self._cached_networks: Dict[str, object] = {}

    @property
    def links(self) -> tuple[str]:
        """Get the links of a certain type."""
        return tuple(self._links.keys())

    @links.setter
    def links(self, link_name: str) -> None:
        """Set the links."""
        self._links[link_name] = {}
        self._back_links[link_name] = {}

    def get_graph(self, link_name):
        """Get the graph."""
        try:
            import networkx as nx
        except ImportError as exc:
            raise ImportError(
                "You need to install networkx to use this function."
            ) from exc
        graph = nx.from_dict_of_lists(self._links[link_name])
        self._cached_networks[link_name] = graph
        return graph

    def _register_link(
        self, link_name: str, source: _LinkNode, target: _LinkNode
    ) -> None:
        """Register a link."""
        if link_name not in self._links:
            self.links = link_name
        if source not in self._links[link_name]:
            self._links[link_name][source] = set()
        if target not in self._back_links[link_name]:
            self._back_links[link_name][target] = set()

    def has_link(
        self, link_name: str, node1: _LinkNode, node2: _LinkNode
    ) -> tuple[bool]:
        """If link exists."""
        data = self._links[link_name]
        node1_to_node2 = (
            False if node1 not in data else node2 in data.get(node1, [])
        )
        node2_to_node1 = (
            False if node2 not in data else node1 in data.get(node2, [])
        )
        return node1_to_node2, node2_to_node1

    def add_a_link(
        self,
        link_name: str,
        source: Node,
        target: Node,
        mutual: bool = False,
    ) -> None:
        """Add a link."""
        self._register_link(link_name, source, target)
        self._links[link_name][source].add(target)
        self._back_links[link_name][target].add(source)
        if mutual:
            self.add_a_link(
                link_name, target=source, source=target, mutual=False
            )

    def remove_a_link(
        self,
        link_name: str,
        source: Node,
        target: Node,
        mutual: bool = False,
    ) -> None:
        """Remove a link."""
        self._links[link_name].get(source, set()).remove(target)
        self._back_links[link_name].get(target, set()).remove(source)
        if mutual:
            self.remove_a_link(
                link_name, target=source, source=target, mutual=False
            )

    def _clean_link_name(
        self, link_name: Optional[str | Iterable[str]]
    ) -> List[str]:
        """清理链接名称"""
        if link_name is None:
            link_name = self.links
        if isinstance(link_name, str):
            link_name = [link_name]
        if not isinstance(link_name, Iterable):
            raise TypeError(f"{link_name} is not an iterable.")
        return link_name

    def clean_links_of(
        self,
        node: _LinkNode,
        link_name: Optional[str] = None,
        direction: Optional[str] = None,
    ) -> None:
        """Clean the links of a node."""
        if direction == "in":
            data = self._back_links
            another_data = self._links
        elif direction == "out":
            data = self._links
            another_data = self._back_links
        elif direction is None:
            self.clean_links_of(node, link_name, direction="in")
            self.clean_links_of(node, link_name, direction="out")
            return
        else:
            raise ValueError(
                f"Invalid direction {direction}, please choose from 'in' or 'out'."
            )
        for name in self._clean_link_name(link_name):
            to_clean = data[name].pop(node, set())
            for another_node in to_clean:
                another_data[name][another_node].remove(node)

    def linked(self, node, link_name, direction):
        """Get the linked nodes."""
        if direction == "in":
            data = self._back_links
        elif direction == "out":
            data = self._links
        else:
            raise ValueError(f"Invalid direction {direction}")
        return data[link_name].get(node, set())


class _LinkProxy:
    """Proxy for linking."""

    def __init__(self, node: Node, model: MainModel) -> None:
        self.node: _LinkNode = node
        self.model: MainModel = model
        self.human: _LinkContainer = model.human

    def get(
        self, link_name: Optional[str] = None, direction: str = "out"
    ) -> Set[Node]:
        """Get the linked nodes."""
        if link_name is None:
            return self.human.links
        agents = self.human.linked(self.node, link_name, direction=direction)
        return ActorsList(self.model, agents)

    def has(self, link_name: str, node: Optional[Node] = None) -> bool:
        """Check if the node has the link."""
        if node is None:
            return link_name in self.human.links
        return self.human.has_link(link_name, self.node, node)

    def to(self, node: Node, link_name: str, mutual: bool = False):
        """Link to the node."""
        self.human.add_a_link(
            link_name=link_name, source=self.node, target=node, mutual=mutual
        )

    def by(self, node: Node, link_name: str, mutual: bool = False):
        """Link by the node."""
        self.human.add_a_link(
            link_name=link_name, source=node, target=self.node, mutual=mutual
        )

    def unlink(self, node: Node, link_name: str, mutual: bool = False):
        """Remove the link."""
        self.human.remove_a_link(
            link_name=link_name, source=self.node, target=node, mutual=mutual
        )

    def clean(
        self, link_name: Optional[str] = None, direction: Optional[str] = None
    ):
        """Clean the links."""
        self.human.clean_links_of(
            self.node, link_name=link_name, direction=direction
        )


class _LinkNode:
    """节点类"""

    @classmethod
    @property
    def breed(cls) -> str:
        """种类"""
        return cls.__name__
