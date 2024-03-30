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

from examples.fire_spread.model import Forest


@pytest.mark.parametrize(
    "parameters",
    [
        {"model": {"density": 0.8, "shape": (100, 100)}, "time": {"end": 50}},
        {"model": {"density": 0.2, "shape": (100, 100)}, "time": {"end": 50}},
        {"model": {"density": 0.8, "shape": (100, 100)}, "time": {"end": 10}},
        {"model": {"density": 0.2, "shape": (100, 100)}, "time": {"end": 10}},
    ],
)
class TestTree:
    """Test tree cell."""

    def test_init(self):
        """Test initialization."""
        tree = Forest()
        assert tree.state == 0
        assert tree is not None

    def test_grow(self):
        """Test grow method."""
        tree = Forest()
        tree.grow()
        assert tree.state == 1

    def test_ignite(self):
        """Test ignite method."""
        tree = Forest()
        tree.ignite()
        assert tree.state == 2

    def test_burning(self):
        """Test burning method."""
        tree = Forest()
        tree.burning()
        assert tree.state == 3


class TestFire:
    """Test fire spread model."""

    def test_init(self, parameters):
        """Test initialization."""
        model = Forest(parameters=parameters)
        assert model is not None

    def test_setup(self, parameters):
        """Test setup."""
        model = Forest(parameters=parameters)
        model.setup()
        assert model.nature.grid.height == parameters["model"]["shape"][0]
        assert model.nature.grid.width == parameters["model"]["shape"][1]
        assert model.time.tick in [10, 50]
