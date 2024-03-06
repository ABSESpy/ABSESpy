#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from typing import List

import pytest

from abses import Actor
from abses.graph import convert_to_networkx
from abses.links import _LinkNode
from abses.main import MainModel
from abses.sequences import ActorsList


# Mocking the LinkNode for testing purposes
class MockNode(_LinkNode):
    """Mock Node for testing purposes."""


class AnotherMockNode(_LinkNode):
    """Another Mock Node for testing purposes."""


@pytest.fixture(name="tres_nodes")
def nodes(model: MainModel) -> List[_LinkNode]:
    """Fixture for creating nodes."""
    return model.agents.create(Actor, num=3)


class TestLinkNode:
    """Test the LinkNode class."""

    def test_link_add(self, tres_nodes: List[_LinkNode]):
        """Test adding a link, happy path."""
        # arrange
        node_1, node_2, _ = tres_nodes

        # action
        node_1.link_to(node_2, "test")

        # assert
        assert isinstance(node_1.linked("test"), ActorsList)
        assert node_2 in node_1.linked("test")
        assert node_1.is_linking_to(node_2, "test")
        assert node_2.is_linked_by(node_1, "test")

    def test_link_delete(self, tres_nodes: List[_LinkNode]):
        """Test deleting a link, happy path."""
        # arrange
        node_1, node_2, _ = tres_nodes
        node_1.link_to(node_2, "test")

        # action
        node_1.unlink_to(node_2, "test")

        # assert
        assert node_1.is_linked_by(node_2, "test")
        assert node_2.is_linking_to(node_1, "test")
        assert not node_1.is_linking_to(node_2, "test")
        assert not node_2.is_linked_by(node_1, "test")

    def test_no_linked_after_die(self, tres_nodes: List[_LinkNode]):
        """Test that the link is deleted after the node dies."""
        # arrange
        node_1, node_2, _ = tres_nodes
        node_1.link_to(node_2, "test")

        # action
        node_1.die()

        # assert
        assert not node_2.is_linked_by(node_1, "test")
        assert not node_1.is_linking_to(node_2, "test")

    def test_unlink(self, tres_nodes: List[_LinkNode]):
        """Test unlinking."""
        # arrange
        node_1, node_2, _ = tres_nodes
        node_1.link_to(node_2, "test")

        # action
        node_1.unlink_with(node_2, "test")

        # assert
        assert not node_1.is_linking_to(node_2, "test")
        assert not node_2.is_linked_by(node_1, "test")


class TestNetworkx:
    """Test linking nodes into networkx."""

    def test_converting_to_networkx(self, tres_nodes: List[_LinkNode]):
        """Test converting to networkx."""
        # arrange
        node_1, node_2, node_3 = tres_nodes
        node_1.link_to(node_2, "test")
        node_2.link_to(node_3, "test")

        # act
        graph = convert_to_networkx(tres_nodes, "test")

        # assert
        assert set(graph.nodes) == set(tres_nodes)
        assert graph.number_of_edges() == 2
