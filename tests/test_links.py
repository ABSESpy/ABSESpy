#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from typing import Dict, Iterator, List, Optional, Tuple, Type

import networkx as nx
import pytest

from abses.links import LinkContainer, LinkNode


# Mocking the LinkNode for testing purposes
class MockNode(LinkNode):
    pass


class AnotherMockNode(LinkNode):
    pass


def test_link_container_initialization():
    container = LinkContainer()
    assert isinstance(container._bipartite, Dict)
    assert isinstance(container._graphs, Dict)


def test_links_property():
    container = LinkContainer()
    assert container.links == ()

    # Mock adding a graph
    container._graphs["mock_link"] = nx.Graph()
    assert container.links == ("mock_link",)


def test_is_bipartite():
    container = LinkContainer()
    node1 = MockNode()
    node2 = MockNode()
    assert not container._is_bipartite(node1, node2)
    node3 = AnotherMockNode()
    assert container._is_bipartite(node1, node3)


def test_is_new_links_graph():
    container = LinkContainer()
    assert container._is_new_links_graph("mock_link")

    # Mock adding a graph
    container._graphs["mock_link"] = nx.Graph()
    assert not container._is_new_links_graph("mock_link")


def test_is_node():
    container = LinkContainer()
    node = MockNode()
    assert container._is_node(node)

    with pytest.raises(TypeError):
        assert container._is_node("not_a_node")


def test_add_new_graph():
    container = LinkContainer()
    container._add_new_graph("mock_link", nx.Graph, True)
    assert "mock_link" in container._graphs

    with pytest.raises(TypeError):
        container._add_new_graph("bad_link", str, True)


def test_is_directed_graph():
    container = LinkContainer()

    # Testing with graph class types
    assert container._is_directed_graph(nx.DiGraph)
    assert not container._is_directed_graph(nx.Graph)

    # Mock adding graphs and testing with link names
    container._add_new_graph("directed_link", nx.DiGraph, True)
    container._add_new_graph("undirected_link", nx.Graph, False)

    assert "directed_link" in container._graphs
    assert container._is_directed_graph("directed_link")
    assert not container._is_directed_graph("undirected_link")
