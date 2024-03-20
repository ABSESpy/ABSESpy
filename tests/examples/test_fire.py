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
    "cfg",
    [
        {"model": {"density": 0.8, "shape": (100, 100)}, "time": {"end": 50}},
        {"model": {"density": 0.2, "shape": (100, 100)}, "time": {"end": 50}},
        {"model": {"density": 0.8, "shape": (100, 100)}, "time": {"end": 10}},
        {"model": {"density": 0.2, "shape": (100, 100)}, "time": {"end": 10}},
    ],
)
class TestFire:
    """Test fire spread model."""

    def test_init(self, cfg):
        """Test initialization."""
        model = Forest(parameters=cfg)
        assert model is not None

    def test_setup(self, cfg):
        """Test setup."""
        model = Forest(parameters=cfg)
        model.run_model()
        assert model.time.tick in [10, 50]
