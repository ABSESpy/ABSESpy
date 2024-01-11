#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from abses import MainModel
from abses.actor import Actor
from abses.sequences import ActorsList


class Farmer(Actor):
    """测试用，另一个类别的主体"""

    def __init__(self, model, observer: bool = True) -> None:
        super().__init__(model, observer)
        self.metric = 0.1


def test_sequences_attributes():
    """测试容器的属性"""
    model = MainModel()
    actors5 = model.agents.create(Actor, 5)
    farmers3 = model.agents.create(Farmer, 3)
    actors5.test = 1
    farmers3.test = -1
    mixed_actors = ActorsList(model=model, objs=[*actors5, *farmers3])
    assert isinstance(actors5, ActorsList)
    assert repr(mixed_actors) == "<ActorsList: (5)Actor; (3)Farmer>"
    assert mixed_actors.to_dict() == {"Actor": actors5, "Farmer": farmers3}
    assert mixed_actors.select("Farmer") == farmers3
    each_one = mixed_actors.select(
        [True, False, False, False, False, True, False, False]
    )
    assert repr(each_one) == "<ActorsList: (1)Actor; (1)Farmer>"


def test_sequences_better():
    model = MainModel(seed=42)
    a_farmer = Farmer(model)
    others = model.agents.create(Farmer, 5)

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

    assert better.random.choice() in better
    # for p in [[0, 0, 0], [-1, -1, -1], [-1, 0, 1], [0, 1, 1]]:
    #     assert better.random.choice(p=p) in better
