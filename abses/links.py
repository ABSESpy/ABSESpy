#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""主体、斑块之间可以产生连接。

Actor, PatchCell can be used to create links.
"""


from __future__ import annotations

import contextlib
from typing import (
    TYPE_CHECKING,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    Set,
    Tuple,
)

with contextlib.suppress(ImportError):
    import networkx as nx
try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

from abses.errors import ABSESpyError
from abses.sequences import ActorsList

if TYPE_CHECKING:
    from abses import MainModel
    from abses.actor import Actor
    from abses.cells import PatchCell

LinkingNode: TypeAlias = "Actor | PatchCell"
Direction: TypeAlias = Optional[Literal["in", "out"]]


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

    def owns_links(
        self, node: LinkingNode, direction: Direction = "out"
    ) -> Tuple[str]:
        """The links a specific node owns."""
        if direction == "out":
            data = self._links
        elif direction == "in":
            data = self._back_links
        elif direction is None:
            links_in = self.owns_links(node, direction="in")
            links_out = self.owns_links(node, direction="out")
            return tuple(set(links_in) | set(links_out))
        else:
            raise ValueError(f"Invalid direction '{direction}'.")
        links = {link for link, agents in data.items() if node in agents}
        return tuple(links)

    def get_graph(self, link_name: str) -> "nx.Graph":  # type: ignore
        """Get the networkx graph.

        Parameters:
            link_name:
                The link name for converting into a graph.

        Raises:
            ImportError:
                If networkx is not installed.
        """
        if "nx" not in globals():
            raise ImportError(
                "You need to install networkx to use this function."
            )
        graph = nx.from_dict_of_lists(self._links[link_name])
        self._cached_networks[link_name] = graph
        return graph

    def _register_link(
        self, link_name: str, source: LinkingNode, target: LinkingNode
    ) -> None:
        """Register a link."""
        if link_name not in self._links:
            self.links = link_name
        if source not in self._links[link_name]:
            self._links[link_name][source] = set()
        if target not in self._back_links[link_name]:
            self._back_links[link_name][target] = set()

    def has_link(
        self, link_name: str, source: LinkingNode, target: LinkingNode
    ) -> tuple[bool]:
        """If any link exists between source and target.

        Parameters:
            link_name:
                The name of the link.
            source:
                The source node.
            target:
                The target node.

        Raises:
            KeyError:
                If the link name does not exist.

        Returns:
            tuple:
                A tuple of two booleans.
                The first element is True if the link exists from source to target.
                The second element is True if the link exists from target to source.
        """
        if link_name not in self.links:
            raise KeyError("No link named {link_name}.")
        data = self._links[link_name]
        to = False if source not in data else target in data.get(source, [])
        by = False if target not in data else source in data.get(target, [])
        return to, by

    def add_a_link(
        self,
        link_name: str,
        source: LinkingNode,
        target: LinkingNode,
        mutual: bool = False,
    ) -> None:
        """Add a link from source to target.

        Parameters:
            link_name:
                The name of the link.
            source:
                The source node.
            target:
                The target node.
            mutual:
                If the link is mutual.
        """
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
        source: LinkingNode,
        target: LinkingNode,
        mutual: bool = False,
    ) -> None:
        """Remove a specific link.

        Parameters:
            link_name:
                The name of the link.
            source:
                The source node.
            target:
                The target node.
            mutual:
                If delete the link mutually.

        Raises:
            ABSESpyError:
                If the link from source to target does not exist.
        """
        if not self.has_link(link_name, source, target)[0]:
            raise ABSESpyError(f"Link from {source} to {target} not found.")
        self._links[link_name].get(source, set()).remove(target)
        self._back_links[link_name].get(target, set()).remove(source)
        if mutual:
            self.remove_a_link(
                link_name, target=source, source=target, mutual=False
            )

    def _clean_link_name(
        self, link_name: Optional[str | Iterable[str]]
    ) -> List[str]:
        """Clean the link name."""
        if link_name is None:
            link_name = self.links
        if isinstance(link_name, str):
            link_name = [link_name]
        if not isinstance(link_name, Iterable):
            raise TypeError(f"{link_name} is not an iterable.")
        return link_name

    def clean_links_of(
        self,
        node: LinkingNode,
        link_name: Optional[str] = None,
        direction: Direction = None,
    ) -> None:
        """Clean the links of a node.

        Parameters:
            node:
                The node to clean the links.
            link_name:
                The name of the link to clean.
                If None, clean all related links for the node.
            direction:
                The direction of the link ('in' or 'out').
                If None, clean both directions (both out links and in links).

        Raises:
            ValueError:
                If the direction is not 'in' or 'out'.
        """
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

    def linked(
        self,
        node: LinkingNode,
        link_name: Optional[str] = None,
        direction: Direction = None,
    ) -> ActorsList[LinkingNode]:
        """Get the linked nodes.

        Parameters:
            node:
                The node to get the linked nodes.
            link_name:
                The name of the link.
                If None, get all type of links.
            direction:
                The direction of the link ('in' or 'out').

        Raises:
            ValueError:
                If the direction is not 'in' or 'out'.

        Returns:
            The linked Actors or PatchCells with the input node.
        """
        link_names = self._clean_link_name(link_name=link_name)
        if direction == "in":
            data = self._back_links
        elif direction == "out":
            data = self._links
        elif direction is None:
            return self.linked(node, link_name, direction="in") | self.linked(
                node, link_name, direction="out"
            )
        else:
            raise ValueError(f"Invalid direction {direction}")
        agents = set()
        for name in link_names:
            agents = agents.union(data[name].get(node, set()))
        return agents


class _LinkProxy:
    """Proxy for linking."""

    def __init__(self, node: LinkingNode, model: MainModel) -> None:
        self.node: _LinkNode = node
        self.model: MainModel = model
        self.human: _LinkContainer = model.human

    def __contains__(self, link_name: str) -> bool:
        """Check if the link exists."""
        return link_name in self.human.links

    def __eq__(self, __value: tuple[str]) -> bool:
        """Check if the links are equal to a set of strings."""
        return set(__value) == set(self.owning())

    def __repr__(self) -> str:
        return str(self.owning())

    def owning(self, direction: Direction = None) -> Tuple[str]:
        """Links that this object has.

        Parameters:
            direction:
                The direction of the link ('in' or 'out').
                If None, return both out links and in links.

        Returns:
            The links that this object has.
        """
        return self.human.owns_links(self.node, direction=direction)

    def get(
        self, link_name: Optional[str] = None, direction: Direction = "out"
    ) -> Set[LinkingNode]:
        """Get the linked nodes."""
        agents = self.human.linked(self.node, link_name, direction=direction)
        return ActorsList(self.model, agents)

    def has(
        self, link_name: str, node: Optional[LinkingNode] = None
    ) -> tuple[bool]:
        """Check if the node has the link.

        Parameters:
            link_name:
                The name of the link.
            node:
                The node to check if it has the link with the current node.
                If None, check if the current node has any link.

        Returns:
            tuple:
                A tuple of two booleans.
                The first element is True if the link exists from me to other.
                The second element is True if the link exists from other to me.
        """
        if node is None:
            has_in = link_name in self.owning("in")
            has_out = link_name in self.owning("out")
            return has_out, has_in
        return self.human.has_link(link_name, self.node, node)

    def to(
        self, node: LinkingNode, link_name: str, mutual: bool = False
    ) -> None:
        """Link to another node.

        Parameters:
            node:
                The node to link to.
            link_name:
                The name of the link.
            mutual:
                If the link is mutual. Defaults to False.
        """
        self.human.add_a_link(
            link_name=link_name, source=self.node, target=node, mutual=mutual
        )

    def by(
        self, node: LinkingNode, link_name: str, mutual: bool = False
    ) -> None:
        """Make this node linked by another node.

        Parameters:
            node:
                The node to link by.
            link_name:
                The name of the link.
            mutual:
                If the link is mutual. Defaults to False.
        """
        self.human.add_a_link(
            link_name=link_name, source=node, target=self.node, mutual=mutual
        )

    def unlink(self, node: LinkingNode, link_name: str, mutual: bool = False):
        """Remove the link between me and another node.

        Parameters:
            node:
                The node to unlink with.
            link_name:
                The name of the link.
            mutual:
                If delete link mutually. Defaults to False.

        Raises:
            ABSESpyError:
                If the link from source to target does not exist.
        """
        self.human.remove_a_link(
            link_name=link_name, source=self.node, target=node, mutual=mutual
        )

    def clean(
        self, link_name: Optional[str] = None, direction: Optional[str] = None
    ):
        """Clean all the related links from this node.

        Parameters:
            link_name:
                The name of the link.
                If None, clean all related links for the node.
            direction:
                The direction of the link ('in' or 'out').
                If None, clean both directions (both out links and in links).

        Raises:
            ValueError:
                If the direction is not 'in' or 'out'.
        """
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
