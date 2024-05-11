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

from examples.hotelling_law.model import Customer, Hotelling


@pytest.fixture(name="hotelling_fixture")
def setup():
    """Create a Hotelling model."""
    model = Hotelling(parameters={"model": {"n_agents": 2}})
    model.setup()
    return model


class TestCustomer:
    @pytest.mark.parametrize(
        "pos, price, prefers",
        [
            ((7, 0), 0, (True, False)),
            ((7, 0), 100, (False, True)),
        ],
    )
    def test_find_preference(self, hotelling_fixture, pos, price, prefers):
        """Test the find_preference method."""
        # arrange
        model = hotelling_fixture
        actor0 = model.actors[0]
        actor1 = model.actors[1]
        actor0.move.to((0, 0))
        actor1.move.to((9, 9))
        actor0.price = price
        c: Customer = model.nature.market.array_cells[pos[0], pos[1]]
        # act
        c.find_preference()
        # assert
        prefer0 = actor0 in c.link.get("prefer", direction="in")
        prefer1 = actor1 in c.link.get("prefer", direction="in")
        assert (prefer0, prefer1) == prefers


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
