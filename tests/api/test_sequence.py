#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/
"""测试列表
"""
from unittest.mock import MagicMock

import numpy as np
import pytest

from abses import MainModel
from abses.actor import Actor
from abses.sequences import ActorsList


class TestSequences:
    """Test Sequence"""

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
        assert mixed_actors.select("Farmer") == farmers3
        each_one = mixed_actors.select(
            [True, False, False, False, False, True, False, False]
        )
        assert repr(each_one) == "<ActorsList: (1)Actor; (1)Farmer>"

    def test_sequences_better(self, model: MainModel, farmer_cls):
        """Test that sequences"""
        # arrange
        a_farmer = model.agents.new(farmer_cls, singleton=True)
        others = model.agents.new(farmer_cls, 5)
        for i, farmer in enumerate(
            others
        ):  # np.array([0.0, 0.1, 0.2, 0.3, 0.4])
            farmer.metric = i / 10
            farmer.test = i
        a_farmer.metric = 0.1

        # act
        better = others.better("metric", than=a_farmer)
        # assert
        assert better == others.select([False, False, True, True, True])
        assert others.better("metric")[0] == others[-1]
        assert others.better("metric", than=0.05) == others.select(
            [False, True, True, True, True]
        )
        assert better.random.choice() in better

    @pytest.mark.parametrize(
        "ufunc, args, kwargs, expected",
        [
            (lambda f: f.metric + 1, (), {}, np.array([1.1, 1.1, 1.1])),
        ],
    )
    def test_apply(
        self, model: MainModel, ufunc, args, kwargs, expected, farmer_cls
    ):
        """Test that applying a function."""
        # assert
        farmers = model.agents.new(farmer_cls, 3)
        actor = model.agents.new(Actor, singleton=True)
        # act
        results = farmers.apply(ufunc, *args, **kwargs)
        expected = farmers.array("metric") + 1
        # assert
        np.testing.assert_array_equal(results, expected)
        farmers.apply(
            lambda f: f.link.to(actor, link_name="test", mutual=True)
        )
        assert actor.link.get("test") == farmers

    @pytest.mark.parametrize(
        "num, index, how, expected",
        [
            (3, 1, "item", 1),
            (3, 1, "random", 1),
            (1, 0, "only", 0),
        ],
    )
    def test_item(self, model: MainModel, num, index, how, expected):
        """Test that the item function."""
        # arrange
        actors = model.agents.new(Actor, num=num)
        expected = actors[expected]
        actors.random.choice = MagicMock(return_value=expected)
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
    def test_bad_item(
        self, model: MainModel, how, num, index, error, to_match
    ):
        """Test that the item function raises an error."""
        # arrange
        actors = model.agents.new(Actor, num=num)
        # act / assert
        with pytest.raises(error, match=to_match):
            actors.item(index=index, how=how)


class TestSequenceAttrGetter:
    """Test Sequence Attribute Getter"""

    def create_actors_with_metric(self, model: MainModel, n: int):
        """Create actors with metric."""
        actors = model.agents.new(Actor, n)
        for i, actor in enumerate(actors):
            actor.test = float(i)
        return actors

    @pytest.mark.parametrize(
        "how, expected",
        [
            ("only", 0.0),
            ("item", 0.0),
            ("random", 0.0),
        ],
    )
    def test_get_only_agent(self, model: MainModel, how, expected):
        """Test that the get_only_agent function."""
        # arrange
        actors = self.create_actors_with_metric(model, 1)
        # act
        result = actors.get("test", how=how)
        # assert
        assert result == actors[0].test == expected

    @pytest.mark.parametrize(
        "how, expected",
        [
            ("item", 0.0),
            ("random", 1.0),
        ],
    )
    def test_get_attr(self, model: MainModel, how, expected):
        """Test that the agg_agents_attr function."""
        # arrange
        actors = self.create_actors_with_metric(model, 3)
        actors.random.choice = MagicMock(return_value=actors[1])
        assert actors.random.choice() == actors[1]

        # act
        result = actors.get("test", how=how)
        # assert
        assert result == expected

    @pytest.mark.parametrize(
        "n, how, error, to_match",
        [
            (1, "not a method", ValueError, "Invalid how method"),
            (0, "only", ValueError, "No agent found."),
            (2, "only", ValueError, "More than one agent."),
        ],
    )
    def test_agg_agents_attr_error(
        self, model: MainModel, n, how, error, to_match
    ):
        """Test that the agg_agents_attr function raises an error."""
        # arrange
        actors = self.create_actors_with_metric(model, n=n)
        # act / assert
        with pytest.raises(error, match=to_match):
            actors.get("test", how=how)
