#!/usr/bin/env python3
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/
"""测试列表"""

import numpy as np
import pytest

from abses import MainModel
from abses.agents.actor import Actor
from abses.agents.sequences import ActorsList
from tests.helper import create_actors_with_metric


class TestSequences:
    """Test Sequence"""

    @pytest.mark.parametrize(
        "selection",
        [
            pytest.param("enabled", id="string"),
            pytest.param({"enabled": True}, id="dict"),
            pytest.param(lambda actor: actor.enabled, id="callable"),
        ],
    )
    def test_select_filter_forms(self, model: MainModel, selection):
        """Select actors with every documented filter form."""
        actors = model.agents.new(Actor, 3)
        actors.update("enabled", [True, False, True])

        selected = actors.select(selection)

        assert list(selected) == [actors[0], actors[2]]

    def test_sequences_attributes(self, model, farmer_cls):
        """测试容器的属性"""
        # arrange
        actors5 = model.agents.new(Actor, 5)
        farmers3 = model.agents.new(farmer_cls, 3)
        actors5.test = 1
        farmers3.test = -1
        mixed_actors = ActorsList(model=model, objs=[*actors5, *farmers3])

        # act / assert
        assert isinstance(actors5, ActorsList)
        assert repr(mixed_actors) == "<ActorsList: (5)Actor; (3)Farmer>"
        assert mixed_actors.to_dict() == {"Actor": actors5, "Farmer": farmers3}
        assert mixed_actors.select(agent_type=farmer_cls) == farmers3

    @pytest.mark.parametrize(
        "than, expected_num",
        [
            (-1.0, 5),
            (0.0, 4),
            (2.0, 2),
            (3.0, 1),
        ],
    )
    def test_sequences_better(self, model: MainModel, than, expected_num):
        """Test that sequences better method works with numeric thresholds."""
        # arrange
        others = create_actors_with_metric(model, 5)

        # act
        better = others.better("test", than=than)
        # assert
        assert len(better) == expected_num

    def test_sequences_better_with_none(self, model: MainModel):
        """Test that better() with than=None returns actors with maximum value."""
        # arrange
        actors = create_actors_with_metric(model, 5)
        # Actor test values are: [0, 1, 2, 3, 4]

        # act
        best = actors.better("test", than=None)

        # assert
        assert len(best) == 1, "Should return only the actor with max value"
        assert best[0].test == 4, "Should return actor with test=4"

    def test_sequences_better_default_none(self, model: MainModel):
        """Test that better() defaults to than=None when not provided."""
        # arrange
        actors = create_actors_with_metric(model, 5)

        # act - call without 'than' parameter
        best = actors.better("test")

        # assert
        assert len(best) == 1
        assert best[0].test == 4

    def test_sequences_better_multiple_max(self, model: MainModel):
        """Test that better() returns all actors with maximum value when there are ties."""
        # arrange
        actors = model.agents.new(Actor, num=5)
        actors[0].test = 1
        actors[1].test = 3
        actors[2].test = 5  # max
        actors[3].test = 2
        actors[4].test = 5  # also max (tie)

        # act
        best = actors.better("test")

        # assert
        assert len(best) == 2, "Should return both actors with max value"
        assert all(actor.test == 5 for actor in best), (
            "All returned actors should have test=5"
        )

    def test_sequences_better_empty_list(self, model: MainModel):
        """Test that better() handles empty lists gracefully."""
        # arrange
        empty_actors = ActorsList(model=model, objs=[])

        # act
        result = empty_actors.better("test")

        # assert
        assert len(result) == 0, "Should return empty list for empty input"
        assert isinstance(result, ActorsList), "Should return ActorsList instance"

    def test_sequences_better_with_actor(self, model: MainModel):
        """Test that better() works when 'than' is an actor."""
        # arrange
        actors = create_actors_with_metric(model, 5)
        reference_actor = actors[2]  # Has test=2

        # act
        better = actors.better("test", than=reference_actor)

        # assert
        assert len(better) == 2, "Should return actors with test > 2"
        assert all(actor.test > 2 for actor in better), "All should have test > 2"
        assert reference_actor not in better, "Reference actor should not be included"

    def test_apply(self, model: MainModel):
        """Test that applying a function."""
        # assert
        actors = create_actors_with_metric(model, 3)
        # act
        results = actors.apply(lambda x: x.test + 1)
        expected = actors.array("test") + 1
        # assert
        np.testing.assert_array_equal(results, expected)

    @pytest.mark.parametrize(
        "num, index, how, expected",
        [
            (3, 1, "item", 1),
            (1, 0, "only", 0),
        ],
    )
    def test_item(self, model: MainModel, num, index, how, expected):
        """Test that the item function."""
        # arrange
        actors = model.agents.new(Actor, num=num)
        expected = actors[expected]
        # act
        result = actors.item(index=index, how=how)
        # assert
        assert result == expected

    @pytest.mark.parametrize(
        "how, num, index, error, to_match",
        [
            ("not a method", 3, 1, ValueError, "Invalid how method"),
            ("only", 2, 0, ValueError, "More than one agent."),
            ("only", 0, 0, ValueError, "No agent found."),
        ],
    )
    def test_bad_item(self, model: MainModel, how, num, index, error, to_match):
        """Test that the item function raises an error."""
        # arrange
        actors = model.agents.new(Actor, num=num)
        # act / assert
        with pytest.raises(error, match=to_match):
            actors.item(index=index, how=how)
