#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
Test fire spread model.
"""

import pytest

from abses import ActorsList
from examples.fire_spread.model import Forest, Tree


@pytest.fixture(name="tree_fixture")
def setup():
    """Create a forest model fully populated with trees"""
    forest = Forest(parameters={"model": {"density": 1, "shape": (100, 100)}})
    forest.setup()
    return forest, forest.nature.forest.array_cells[51, 51]


class TestTree:
    """Test tree cell."""

    def test_init(self):
        """Test initialization."""
        tree = Tree()
        assert tree.state == 0
        assert tree is not None

    def test_setup(self, tree_fixture):
        """Test initialization."""
        forest, tree = tree_fixture
        xarr = forest.nature.forest.get_xarray()
        assert tree.state == 1
        assert tree is not None
        assert forest is not None
        assert (xarr == 2).mean() == 1 / 100

    def test_states(self, tree_fixture):
        """Test grow method."""
        _, tree = tree_fixture
        tree.ignite()
        assert tree.state == 2
        tree.burning()
        assert tree.state == 3


@pytest.mark.parametrize(
    "parameters",
    [
        {"model": {"density": 0.8, "shape": (25, 25)}},
        {"model": {"density": 0.4, "shape": (25, 25)}},
    ],
)
class TestForest:
    """Test fire spread model."""

    @pytest.fixture(name="forest_fixture")
    def setup(self, parameters):
        """Create a forest model with given parameters"""
        model = Forest(parameters=parameters)
        model.setup()
        return model

    def test_setup(self, forest_fixture):
        """Test setup."""
        forest = forest_fixture
        x = forest.nature.forest.width
        y = forest.nature.forest.height
        assert forest is not None
        assert x == 25
        assert y == 25
        assert forest.num_trees == int(x * y * forest.params.density)
        assert (
            all(
                ActorsList(
                    forest, forest.nature.forest.array_cells[:, 0]
                ).apply(lambda t: t.state in [0, 2])
            )
            is True
        )
        assert (
            any(
                ActorsList(
                    forest, forest.nature.forest.array_cells[:, 1]
                ).apply(lambda t: t.state in [2, 3])
            )
            is False
        )

    def test_step(self, forest_fixture):
        """Test step."""
        forest = forest_fixture
        forest.setup()
        forest.step()
        assert (
            any(
                ActorsList(
                    forest, forest.nature.forest.array_cells[:, 1]
                ).apply(lambda t: t.state in [2, 3])
            )
            is True
        )
        assert (
            any(
                ActorsList(
                    forest, forest.nature.forest.array_cells[:, 2]
                ).apply(lambda t: t.state in [2, 3])
            )
            is True
        )
