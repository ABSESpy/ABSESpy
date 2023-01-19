#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import numpy as np

from abses.actor import Actor
from abses.sequences import ActorsList

from .create_tested_instances import Admin, Farmer, simple_main_model


def test_sequences_attributes():
    model = simple_main_model(test_sequences_attributes)
    actors5 = model.agents.create(Actor, 5)
    farmers3 = model.agents.create(Farmer, 3)
    actors5.test = 1
    farmers3.test = -1
    mixed_actors = ActorsList(model=model, objs=[*actors5, *farmers3])
    assert isinstance(actors5, ActorsList)
    assert mixed_actors.__repr__() == "<(5)Actor; (3)Farmer>"
    assert mixed_actors.to_dict() == {"Actor": actors5, "Farmer": farmers3}
    assert all(
        mixed_actors.on_earth
        == [False, False, False, False, False, False, False, False]
    )
    assert len(mixed_actors.now()) == 0
    assert mixed_actors.select("Farmer") == farmers3
    each_one = mixed_actors.select(
        [True, False, False, False, False, True, False, False]
    )
    assert each_one.__repr__() == "<(1)Actor; (1)Farmer>"
    assert mixed_actors.array("test").sum() == mixed_actors.test.sum()
    # 设置属性
    mixed_actors.testing = "testing"
    for actor in mixed_actors:
        assert actor.testing == "testing"


# def test_sequences_random_choose():
#     assert


def test_sequences_better():
    model = simple_main_model(test_sequences_better)
    a_farmer = Farmer(model)
    others = ActorsList(model, 5, Farmer)

    # np.array([0.0, 0.1, 0.2, 0.3, 0.4])
    for i, farmer in enumerate(others):
        farmer.metric = i / 10
        farmer.test = i
    a_farmer.metric = 0.1

    better = others.better("metric", than=a_farmer)
    assert better == others.select([False, False, True, True, True])
    assert others.better("metric")[0] == others[-1]
    assert others.better("metric", than=0.05) == others.select(
        [False, True, True, True, True]
    )

    assert better.random_choose() in better
    for p in [[0, 0, 0], [-1, -1, -1], [-1, 0, 1], [0, 1, 1]]:
        assert better.random_choose(p=p) in better
