#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import numpy as np

from abses import MainModel
from abses.nature import PatchModule

from .fixtures import Admin, Farmer

selection = {
    "breed": "Farmer",
    "id": 3,
}


def test_human_attributes():
    model = MainModel()
    human = model.human
    assert human.agents is model.agents
    assert len(human.actors()) == 0
    human.agents.create(Farmer, 5)
    model.agents.create(Admin, 5)
    assert len(human.agents) == 10


def test_human_define():
    model = MainModel()
    human = model.human
    farmers = human.agents.create(Farmer, 5)
    admins = model.agents.create(Admin, 5)

    farmers.update("test", np.arange(5))
    admins.update("test", np.arange(5))

    human.define("test", "Farmer")
    assert human.actors("test") == farmers
    human.agents.remove(farmers[0])
    assert human.actors("test") == farmers[1:]
