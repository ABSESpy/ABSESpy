#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""测试链接
"""

from typing import List

import pytest

from abses import Actor
from abses._bases.errors import ABSESpyError
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
    return model.agents.new(Actor, num=3)


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


class TestLinkProxy:
    """Test linking methods in proxy."""

    @pytest.mark.parametrize(
        "links, mutual, to_or_by, expected",
        [
            (("test", "test1", "test2"), True, "to", (True, True)),
            (("test", "test1", "test2"), False, "to", (True, False)),
            (("test", "test", "test2"), False, "to", (True, False)),
            (("test", "test1", "test1"), True, "to", (True, True)),
            (("test", "test1", "test2"), True, "by", (True, True)),
            (("test", "test1", "test2"), False, "by", (False, True)),
            (("test", "test", "test2"), False, "by", (False, True)),
            (("test", "test1", "test1"), True, "by", (True, True)),
        ],
    )
    def test_link_to_or_by(
        self,
        tres_nodes: List[Actor],
        links,
        mutual,
        to_or_by,
        container: _LinkContainer,
        expected,
    ):
        """Test linking to"""
        # arrange
        a1, a2, a3 = tres_nodes
        link1, link2, link3 = links

        # act
        getattr(a1.link, to_or_by)(a2, link1, mutual=mutual)
        getattr(a1.link, to_or_by)(a3, link2, mutual=mutual)
        getattr(a2.link, to_or_by)(a3, link3, mutual=mutual)

        # assert
        assert a1.link == {link1, link2}
        assert a2.link == {link1, link3}
        assert a3.link == {link2, link3}
        assert set(container.links) == {link1, link2, link3}
        assert container.has_link(link1, a1, a2) == expected
        assert container.has_link(link2, a1, a3) == expected
        assert container.has_link(link3, a2, a3) == expected

    @pytest.mark.parametrize(
        "mutual, to_or_by, expected",
        [
            (True, "to", (True, True)),
            (False, "to", (True, False)),
            (True, "by", (True, True)),
            (False, "by", (False, True)),
        ],
    )
    def test_has(self, tres_nodes: List[Actor], mutual, to_or_by, expected):
        """Test that if a node has a link, or has link with another node."""
        # arrange
        node1, node2, _ = tres_nodes
        getattr(node1.link, to_or_by)(node2, "test", mutual=mutual)

        # act / assert
        assert node1.link.has("test", node2) == expected
        assert node1.link.has("test") == expected

    @pytest.mark.parametrize(
        "to_or_by, mutuals, link_name, direction, expected",
        [
            (("to", "to"), (True, True), "t2", "out", (True, False)),
            (("by", "to"), (False, True), "t2", "out", (False, False)),
            (("by", "to"), (True, True), "t2", "out", (True, False)),
            (("by", "to"), (False, True), "t2", "in", (True, False)),
            (("by", "to"), (False, True), ["t2", "t3"], "in", (True, True)),
            (("by", "to"), (False, True), ["t2", "t3"], "out", (False, True)),
            (("by", "to"), (True, True), ["t2", "t3"], "in", (True, True)),
            (("by", "to"), (True, True), ["t2", "t3"], "out", (True, True)),
        ],
    )
    def test_get_link(
        self,
        tres_nodes: List[Actor],
        to_or_by,
        mutuals,
        expected,
        link_name,
        direction,
    ):
        """testing get linked actors / cells."""
        # arrange
        node1, node2, node3 = tres_nodes
        tob2, tob3 = to_or_by
        m2, m3 = mutuals
        getattr(node1.link, tob2)(node2, link_name="t2", mutual=m2)
        getattr(node1.link, tob3)(node3, link_name="t3", mutual=m3)

        # act
        results = node1.link.get(link_name=link_name, direction=direction)

        # assert
        assert expected == (node2 in results, node3 in results)

    def test_bad_get(self, tres_nodes: List[Actor]):
        """Test that the get method raises an error if the link is not found."""
        # arrange
        node1, _, _ = tres_nodes

        # act / assert
        with pytest.raises(KeyError, match="test"):
            node1.link.get("test")
        assert not node1.link.get("test", default=True)

    @pytest.mark.parametrize(
        "link_name, direction, expected_2, expected_3",
        [
            ("test2", "in", (True, False), (True, True)),
            ("test2", "out", (False, True), (True, True)),
            ("test2", None, (False, False), (True, True)),
            (["test2", "test3"], "in", (True, False), (True, False)),
            (["test2", "test3"], "out", (False, True), (False, True)),
            (["test2", "test3"], None, (False, False), (False, False)),
            (None, None, (False, False), (False, False)),
        ],
    )
    def test_clean(
        self,
        tres_nodes: List[Actor],
        link_name,
        direction,
        expected_2,
        expected_3,
    ):
        """testing delete all links."""
        # arrange
        node1, node2, node3 = tres_nodes
        node1.link.to(node2, "test2", True)
        node1.link.to(node3, "test3", True)
        # act
        node1.link.clean(link_name=link_name, direction=direction)
        # assert
        assert node1.link.has("test2") == expected_2
        assert node1.link.has("test3") == expected_3

    @pytest.mark.parametrize(
        "mutual, expected",
        [
            (False, (False, True)),
            (True, (False, False)),
        ],
    )
    def test_unlink(self, tres_nodes: List[Actor], expected, mutual):
        """testing delete a specific link."""
        # arrange
        node1, node2, node3 = tres_nodes
        node1.link.to(node2, "test", mutual=True)
        # act
        node1.link.unlink(node2, "test", mutual=mutual)
        with pytest.raises(ABSESpyError, match="not found."):
            node1.link.unlink(node3, "test", mutual=True)
        # assert
        assert node1.link.has("test", node2) == expected
