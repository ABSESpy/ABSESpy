#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/
"""测试列表
"""
import numpy as np
import pytest

from abses import MainModel
from abses.actor import Actor
from abses.sequences import ActorsList


class Farmer(Actor):
    """测试用，另一个类别的主体"""

    def __init__(self, model, observer: bool = True) -> None:
        super().__init__(model, observer)
        self.metric = 0.1


class TestSequences:
    """Test Sequence"""

    def test_sequences_attributes(self, model):
        """测试容器的属性"""
        # arrange
        actors5 = model.agents.new(Actor, 5)
        farmers3 = model.agents.new(Farmer, 3)
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

    def test_sequences_better(self, model: MainModel):
        """Test that sequences"""
        # arrange
        a_farmer = model.agents.new(Farmer, singleton=True)
        others = model.agents.new(Farmer, 5)
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
    def test_apply(self, model: MainModel, ufunc, args, kwargs, expected):
        """Test that applying a function."""
        # assert
        farmers = model.agents.new(Farmer, 3)
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
