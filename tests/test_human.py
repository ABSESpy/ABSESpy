#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import numpy as np

from abses import MainModel

selection = {
    "breed": "Farmer",
    "id": 3,
}


def test_human_attributes(farmer_cls, admin_cls):
    """测试人类模块的属性"""
    model = MainModel()
    human = model.human
    assert human.agents is model.agents
    assert len(human.actors()) == 0
    human.agents.create(farmer_cls, 5)
    model.agents.create(admin_cls, 5)
    assert len(human.agents) == 10


def test_human_define(farmer_cls, admin_cls):
    """测试人口的定义"""
    model = MainModel()
    human = model.human
    farmers = human.agents.create(farmer_cls, 5)
    admins = model.agents.create(admin_cls, 5)

    farmers.update("test", np.arange(5))
    admins.update("test", np.arange(5))

    human.define("test", "Farmer")
    assert human.actors("test") == farmers
    human.agents.remove(farmers[0])
    assert human.actors("test") == farmers[1:]
