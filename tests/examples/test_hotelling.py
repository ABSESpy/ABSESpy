#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
Test Hotelling Law model.
"""

import pytest

from examples.hotelling_law.model import Customer, Hotelling, Shop


@pytest.fixture(name="hotelling_fixture")
def setup():
    """Create a Hotelling model."""
    model = Hotelling(parameters={"model": {"n_agents": 2}})
    model.setup()
    return model


class TestCustomer:
    def test_find_preference(self, hotelling_fixture):
        """Test the find_preference method."""
        model = hotelling_fixture
        model.actors[0].move.to((0, 0))
        model.actors[1].move.to((9, 9))
        c = model.nature.market.array_cells[
            7, 0
        ]  # np.ndarray[8, 0] equivalent to position (0, 1)
        c.find_preference()
        assert c.link.get("prefer", direction="in")[0].pos == (0, 0)
        model.actors[0].price = 1000
        c.find_preference()
        assert c.link.get("prefer", direction="in")[1].pos == (9, 9)


class TestShop:
    def test_area_count(self, hotelling_fixture):
        """Test the area_count method."""
        model = hotelling_fixture
        model.recalculate_preferences()
        shop1 = model.actors[0]

        assert model is not None
        assert shop1.area_count is not None

    # TODO: Add mroe test for the price and position adjustment functionalities


class TestHotelling:
    def test_recalculate_preferences(self, hotelling_fixture):
        """Test the recalculate_preferences method."""
        model = hotelling_fixture
        model.actors[0].move.to((0, 0))
        model.actors[1].move.to((1, 1))
        model.recalculate_preferences()
        assert model.actors[1].area_count > model.actors[0].area_count

    # TODO: Add more tests for setup and step procedures
