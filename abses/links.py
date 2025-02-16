#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""Actor, PatchCell can be used to create links."""

from __future__ import annotations

import contextlib
from abc import abstractmethod
from functools import cached_property
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    Set,
    Tuple,
    Union,
    cast,
    overload,
)

import numpy as np
import pandas as pd
from loguru import logger

with contextlib.suppress(ImportError):
    import networkx as nx
try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

from abses._bases.errors import ABSESpyError
from abses.sequences import ActorsList
from abses.tools.func import make_list

if TYPE_CHECKING:
    from abses import MainModel
    from abses.actor import Actor
    from abses.cells import PatchCell
    from abses.container import UniqueID
    from abses.sequences import Link

LinkingNode: TypeAlias = "Actor | PatchCell"
Direction: TypeAlias = Optional[Literal["in", "out"]]
__built_in_targets__: Tuple[str, str] = ("cell", "actor")
TargetName: TypeAlias = Union[Literal["cell", "actor", "self"], str]
AttrGetter: TypeAlias = Union["Link", ActorsList["Link"]]


def get_node_unique_id(node: Any) -> UniqueID:
    """Gets a unique ID for a node when importing actors from graph.

    Args:
        node: The node to get unique ID for.

    Returns:
        str or int: The unique ID for the node.

    Raises:
        Warning: If using repr() for non-string/int node types.
    """
    if not isinstance(node, (str, int)):
        logger.warning(f"Using repr for '{type(node)}' unique ID to create actor.")
        return repr(node)
    return node


class _LinkContainer:
    """Container for managing links between nodes.

    Attributes:
        _back_links: Dictionary storing incoming links.
        _links: Dictionary storing outgoing links.
        _cached_networks: Dictionary storing cached network graphs.
    """

    def __init__(self) -> None:
        self._back_links: Dict[str, Dict[LinkingNode, Set]] = {}
        self._links: Dict[str, Dict[LinkingNode, Set]] = {}
        self._cached_networks: Dict[str, object] = {}

    @property
    def links(self) -> Tuple[str, ...]:
        """Get the links of a certain type."""
        return tuple(self._links.keys())

    def _add_a_link_name(self, link_name: str) -> None:
        """Add a link."""
        self._links[link_name] = {}
        self._back_links[link_name] = {}

    def owns_links(
        self, node: LinkingNode, direction: Direction = "out"
    ) -> Tuple[str, ...]:
        """Gets all link types that a specific node participates in.

        Args:
            node: The node to check links for.
            direction: Direction of links to check:
                - "out": outgoing links
                - "in": incoming links
                - None: both directions

        Returns:
            Tuple of link type names.

        Raises:
            ValueError: If direction is invalid.
        """
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

    @overload
    def get_graph(self, link_name: str, directions: bool = False) -> "nx.Graph": ...

    @overload
    def get_graph(self, link_name: str, directions: bool = True) -> "nx.DiGraph": ...

    def get_graph(
        self, link_name: str, directions: bool = False
    ) -> "nx.Graph | nx.DiGraph":
        """Converts links of specified type to a networkx graph.

        Args:
            link_name: The link type to convert.
            directions: If True, returns directed graph. If False, returns undirected.

        Returns:
            A networkx Graph or DiGraph object.

        Raises:
            ImportError: If networkx is not installed.
        """
        if "nx" not in globals():
            raise ImportError("You need to install networkx to use this function.")
        creating_using = nx.DiGraph if directions else nx.Graph
        graph = nx.from_dict_of_lists(self._links[link_name], creating_using)
        self._cached_networks[link_name] = graph
        return graph

    def _register_link(
        self, link_name: str, source: LinkingNode, target: LinkingNode
    ) -> None:
        """Register a link."""
        if link_name not in self._links:
            self._add_a_link_name(link_name)
        if source not in self._links[link_name]:
            self._links[link_name][source] = set()
        if target not in self._back_links[link_name]:
            self._back_links[link_name][target] = set()

    def has_link(
        self, link_name: str, source: LinkingNode, target: LinkingNode
    ) -> Tuple[bool, bool]:
        """Checks if links exist between source and target nodes.

        Args:
            link_name: The link type to check.
            source: The source node.
            target: The target node.

        Returns:
            Tuple of (has_outgoing, has_incoming) booleans where:
                - has_outgoing: True if link exists from source to target
                - has_incoming: True if link exists from target to source

        Raises:
            KeyError: If link_name does not exist.
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
        """Creates a new link between nodes.

        Args:
            link_name: The type of link to create.
            source: The source node.
            target: The target node.
            mutual: If True, creates links in both directions.
        """
        self._register_link(link_name, source, target)
        self._links[link_name][source].add(target)
        self._back_links[link_name][target].add(source)
        if mutual:
            self.add_a_link(link_name, target=source, source=target, mutual=False)

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
            self.remove_a_link(link_name, target=source, source=target, mutual=False)

    def _clean_link_name(self, link_name: Optional[str | Iterable[str]]) -> List[str]:
        """Clean the link name."""
        if link_name is None:
            link_name = self.links
        if isinstance(link_name, str):
            link_name = [link_name]
        if not isinstance(link_name, Iterable):
            raise TypeError(f"{link_name} is not an iterable.")
        return list(link_name)

    def clean_links_of(
        self,
        node: LinkingNode,
        link_name: Optional[str] = None,
        direction: Direction = None,
    ) -> None:
        """Removes all links associated with a node.

        Args:
            node: The node to clean links for.
            link_name: The type of links to clean. If None, cleans all types.
            direction: Direction of links to clean:
                - "in": incoming links
                - "out": outgoing links
                - None: both directions

        Raises:
            ValueError: If direction is invalid.
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
        default: Any = ...,
    ) -> Set[LinkingNode]:
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
            in_links = self.linked(node, link_name, direction="in")
            out_links = self.linked(node, link_name, direction="out")
            return in_links | out_links
        else:
            raise ValueError(f"Invalid direction {direction}")
        agents: Set[LinkingNode] = set()
        for name in link_names:
            if name not in data and default is not ...:
                continue
            agents = agents.union(data[name].get(node, set()))
        return agents

    def _check_is_node(
        self,
        node: UniqueID | LinkingNode,
        mapping_dict: Optional[Dict[UniqueID, Actor]] = None,
    ) -> LinkingNode:
        if mapping_dict:
            unique_id = get_node_unique_id(node)
            node = mapping_dict[unique_id]
        if not isinstance(node, _LinkNode):
            raise TypeError(f"Invalid node type {type(node)}, mapping: {mapping_dict}.")
        return node

    def add_links_from_graph(
        self,
        graph: "nx.Graph",
        link_name: str,
        mapping_dict: Optional[Dict[UniqueID, Actor]] = None,
        mutual: Optional[bool] = None,
    ) -> None:
        """Add links from graph."""
        if mutual is None:
            mutual = not isinstance(graph, nx.DiGraph)
        if mapping_dict is None:
            mapping_dict = {}
        edges = 0
        for source, targets in nx.to_dict_of_lists(graph).items():
            source = self._check_is_node(source, mapping_dict)
            for target in targets:
                target = self._check_is_node(target, mapping_dict)
                self.add_a_link(link_name, source, target, mutual=mutual)
                edges += 1
        logger.info(f"Imported links {edges} links from graph {graph}.")


class _LinkProxy:
    """Proxy class for managing links on a node.

    Provides convenient methods for creating, checking and removing links.

    Attributes:
        node: The node this proxy manages links for.
        model: The main model instance.
        human: The link container instance.
    """

    def __init__(self, node: LinkingNode, model: MainModel) -> None:
        self.node: LinkingNode = node
        self.model: MainModel = model
        self.human: _LinkContainer = model.human

    def __contains__(self, link_name: str) -> bool:
        """Check if the link exists."""
        return link_name in self.human.links

    def __eq__(self, __value: object) -> bool:
        """Check if the links are equal to a set of strings."""
        if not isinstance(__value, Iterable):
            return NotImplemented
        return set(__value) == set(self.owning())

    def __repr__(self) -> str:
        return str(self.owning())

    def owning(self, direction: Direction = None) -> Tuple[str, ...]:
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
        self,
        link_name: Optional[str] = None,
        direction: Direction = "out",
        default: Any = ...,
    ) -> ActorsList[LinkingNode]:
        """Gets nodes linked to this node.

        Args:
            link_name: Type of links to get. If None, gets all types.
            direction: Direction of links to get:
                - "out": outgoing links
                - "in": incoming links
                - None: both directions
            default: Value to return if link type not found.

        Returns:
            List of linked nodes.
        """
        agents = self.human.linked(
            self.node, link_name, direction=direction, default=default
        )
        return ActorsList(self.model, agents)

    def has(
        self, link_name: str, node: Optional[LinkingNode] = None
    ) -> Tuple[bool, bool]:
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

    def to(self, node: LinkingNode, link_name: str, mutual: bool = False) -> None:
        """Creates an outgoing link to another node.

        Args:
            node: The target node to link to.
            link_name: The type of link to create.
            mutual: If True, creates links in both directions.
        """
        self.human.add_a_link(
            link_name=link_name, source=self.node, target=node, mutual=mutual
        )

    def by(self, node: LinkingNode, link_name: str, mutual: bool = False) -> None:
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

    def clean(self, link_name: Optional[str] = None, direction: Direction = None):
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
        self.human.clean_links_of(self.node, link_name=link_name, direction=direction)


class _BreedDescriptor:
    """A descriptor to get the breed of a node."""

    def __get__(self, _: Any, owner: Any) -> str:
        return owner.__name__ if owner else self.__class__.__name__


class _LinkNode:
    """Base class for nodes that can be linked.

    Provides core functionality for managing attributes and links between nodes.

    Attributes:
        unique_id: Unique identifier for the node.
        breed: The breed/type of the node.
        link: Proxy for managing links.
    """

    unique_id: int = -1
    breed = _BreedDescriptor()

    @abstractmethod
    def _target_is_me(self, target: Optional[TargetName]) -> bool:
        """Check if the target is me."""

    @classmethod
    def viz_attrs(cls, **kwargs) -> Dict[str, Any]:
        """Return the attributes for viz."""
        maker = getattr(cls, "marker", "o")
        return {
            "marker": maker,
            "color": getattr(cls, "color", "black"),
            "alpha": getattr(cls, "alpha", 1.0),
        } | kwargs

    @cached_property
    def link(self) -> _LinkProxy:
        """A proxy which can be used to manipulate the links:

        1. `link.to()`: creates a new link from this actor to another.
        2. `link.by()`: creates a new link from another to this actor.
        3. `link.get()`: gets the links of this actor.
        4. `link.has()`: checks if there is a link between this actor and another.
        5. `link.unlink()`: removes a link between this actor and another.
        6. `link.clean()`: removes all links of this actor.
        """
        return _LinkProxy(cast(LinkingNode, self), getattr(self, "model"))

    def has(self, attr: str, raise_error: bool = False) -> bool:
        """Check if the attribute exists in the current node.

        Args:
            attr:
                The name of the attribute to check.
            raise_error:
                If True, raise an error if the attribute does not exist.

        Returns:
            bool:
                True if the attribute exists, False otherwise.
        """
        # If the attribute is not a string, raise an error.
        if not isinstance(attr, str):
            raise TypeError(f"The attribute to check {attr} is not string.")
        if attr.startswith("_"):
            # protected attribute
            flag = False
        else:
            flag = hasattr(self, attr)
        if flag:
            return True
        if raise_error:
            raise AttributeError(f"'{self}' doesn't have attribute '{attr}'.")
        return False

    def _redirect(self, target: Optional[TargetName]) -> _LinkNode:
        """Redirect the target.

        Args:
            target:
                The target to redirect to.

        Returns:
            The redirected target.
        """
        if self._target_is_me(target):
            return self
        if isinstance(target, str) and any(self.link.has(link_name=target)):
            return cast(LinkingNode, self.link.get(link_name=target))
        raise ABSESpyError(f"Unknown target {target}.")

    def _setattr(
        self, attr: str, value: Any, target: Optional[TargetName], new: bool = False
    ) -> None:
        """Set the attribute on the current node."""
        if attr.startswith("_"):
            raise AttributeError(f"Attribute '{attr}' is protected.")
        if new:
            setattr(self, attr, value)
            return
        if not self.has(attr):
            raise AttributeError(
                f"Attribute '{attr}' not found in {self}, please set 'new=True' to create a new attribute."
            )
        if self._target_is_me(target):
            setattr(self, attr, value)
            return
        raise ABSESpyError(
            f"The target '{target}' is not 'self' set when '{self}' already has attr '{attr}'."
        )

    def get(
        self, attr: str, target: Optional[TargetName] = None, default: Any = ...
    ) -> Any:
        """Gets an attribute value from this node or a target.

        Args:
            attr: Name of attribute to get.
            target: Where to get the attribute from:
                - None: try self first, then default target
                - "self": get from this node only
                - other targets: get from linked target
            default: Value to return if attribute not found.

        Returns:
            The attribute value.

        Raises:
            AttributeError: If attribute not found and no default provided.
        """
        if self._target_is_me(target):
            if default is ...:
                return getattr(self, attr)
            return getattr(self, attr, default)
        if target is not None:
            target_obj = self._redirect(target=target)
            return target_obj.get(attr, target="self", default=default)
        if self.has(attr, raise_error=False):
            return getattr(self, attr)
        if default is not ...:
            return default
        target_obj = self._redirect(target=target)
        try:
            return target_obj.get(attr=attr, target="self", default=default)
        except AttributeError as exc:
            raise AttributeError(
                f"Neither {self} nor {target_obj} has attribute {attr}."
            ) from exc

    def set(
        self,
        attr: str,
        value: Any,
        target: Optional[TargetName] = None,
        new: bool = False,
    ) -> None:
        """Sets an attribute value on this node or a target.

        Args:
            attr: Name of attribute to set.
            value: Value to set.
            target: Where to set the attribute:
                - None: try self first, then default target
                - "self": set on this node only
                - other targets: set on linked target
            new: If True, allows creating new attributes.

        Raises:
            AttributeError: If attribute doesn't exist and new=False.
            TypeError: If attr is not a string.
            ABSESpyError: If target is invalid or attribute is protected.
        """
        if self._target_is_me(target):
            self._setattr(attr, value, target="self", new=new)
            return
        if target is None and new:
            self._setattr(attr, value, target="self", new=new)
            return
        if target is not None:
            self._redirect(target=target).set(attr, value, target="self", new=new)
            return
        if self.has(attr):
            self._setattr(attr, value, target="self")
            return
        target_obj = self._redirect(target="self")
        if hasattr(target_obj, attr):
            target_obj.set(attr, value, target="self", new=new)
            return
        raise AttributeError(f"Neither {self} nor {target_obj} has attribute '{attr}'.")

    def summary(
        self, coords: bool = False, attrs: Optional[Iterable[str] | str] = None
    ) -> pd.Series:
        """Returns a summary of the object."""
        geo_type = self.get("geo_type")
        if geo_type in ("Point", "Cell"):
            a, b = self.get("coordinate" if coords else "pos")
        else:
            a, b = np.nan, np.nan
        result = {
            "breed": self.breed,
            "geo_type": geo_type,
            "x" if coords else "row": a,
            "y" if coords else "col": b,
        }
        result.update({attr: self.get(attr) for attr in make_list(attrs)})
        return pd.Series(result, name=self.unique_id)


class _LinkNodeCell(_LinkNode):
    """PatchCell"""

    _default_redirect_target = "actor"

    def _target_is_me(self, target: Optional[TargetName]) -> bool:
        """Check if the target is me."""
        return target in ("self", "cell")

    def _redirect(self, target: Optional[TargetName]) -> _LinkNode:
        """By default, redirect to the agents list of this cell."""
        if target == self._default_redirect_target or target is None:
            return self.get("agents", target="self")
        return super()._redirect(target)


class _LinkNodeActor(_LinkNode):
    _default_redirect_target = "cell"

    def _target_is_me(self, target: Optional[TargetName]) -> bool:
        """Check if the target is me."""
        return target in ("self", "actor")

    def _redirect(self, target: Optional[TargetName]) -> _LinkNode:
        """Redirect the target.

        Args:
            target:
                The target to redirect to.

        Returns:
            The redirected target.
        """
        if target == self._default_redirect_target or target is None:
            return self.get("at", target="self")
        return super()._redirect(target)
