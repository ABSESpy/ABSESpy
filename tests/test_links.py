#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from typing import List

import pytest

from abses import Actor
from abses.links import _LinkContainer, _LinkNode
from abses.main import MainModel


# Mocking the LinkNode for testing purposes
class MockNode(_LinkNode):
    """Mock Node for testing purposes."""


class AnotherMockNode(_LinkNode):
    """Another Mock Node for testing purposes."""


@pytest.fixture(name="tres_nodes")
def nodes(model: MainModel) -> List[Actor]:
    """Fixture for creating nodes."""
    return model.agents.create(Actor, num=3)


@pytest.fixture(name="container")
def mock_container(model: MainModel) -> _LinkContainer:
    """test link container"""
    return model.human


class TestLinkContainer:
    """Test the LinkNode class."""

    def test_link_add(
        self, tres_nodes: List[Actor], container: _LinkContainer
    ):
        """Test adding a link, happy path."""
        # arrange
        node_1, node_2, _ = tres_nodes

        # action
        container.add_a_link("test", node_1, node_2)

        # assert
        assert "test" in container.links
        assert any(container.has_link("test", node_1, node_2))
        assert not all(container.has_link("test", node_1, node_2))

    @pytest.mark.parametrize(
        "mutual, expected",
        [
            (True, (False, False)),
            (False, (False, True)),
        ],
    )
    def test_link_delete(
        self,
        tres_nodes: List[Actor],
        container: _LinkContainer,
        mutual,
        expected,
    ):
        """Test deleting a link, happy path."""
        # arrange
        node_1, node_2, _ = tres_nodes
        container.add_a_link("test", node_1, node_2, mutual=True)

        # action
        container.remove_a_link("test", node_1, node_2, mutual=mutual)

        # assert
        assert "test" in container.links
        assert container.has_link("test", node_1, node_2) == expected

    @pytest.mark.parametrize(
        "direction, expected",
        [
            ("in", (True, False)),
            ("out", (False, True)),
            (None, (False, False)),
        ],
        ids=[
            "Direction = in",
            "Direction = out",
            "Direction = None",
        ],
    )
    def test_clean_links(
        self,
        tres_nodes: List[Actor],
        container: _LinkContainer,
        direction,
        expected,
    ):
        """Test cleaning the links."""
        # arrange
        node_1, node_2, _ = tres_nodes
        container.add_a_link("test", node_1, node_2, mutual=True)

        # action
        container.clean_links_of(node_1, "test", direction=direction)

        # assert
        assert container.has_link("test", node_1, node_2) == expected

    def test_no_linked_after_die(
        self, tres_nodes: List[Actor], container: _LinkContainer
    ):
        """Test that the link is deleted after the node dies."""
        # arrange
        node_1, node_2, _ = tres_nodes
        container.add_a_link("test", node_1, node_2, mutual=True)

        # action
        node_1.die()

        # assert
        assert container.has_link("test", node_1, node_2) == (False, False)


class TestNetworkx:
    """Test linking nodes into networkx."""

    def test_converting_to_networkx(
        self, tres_nodes: List[Actor], container: _LinkContainer
    ):
        """Test converting to networkx."""
        # arrange
        node_1, node_2, node_3 = tres_nodes
        container.add_a_link("test", node_1, node_2, mutual=True)
        container.add_a_link("test", node_2, node_3, mutual=True)

        # act
        graph = container.get_graph("test")

        # assert
        assert set(graph.nodes) == set(tres_nodes)
        assert graph.number_of_edges() == 2
