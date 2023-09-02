#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import numpy as np

from abses import MainModel
from abses.human import HumanModule
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
    assert len(human.actors) == 0
    human.agents.create(Farmer, 5)
    model.agents.create(Admin, 5)
    assert len(human.agents) == 10
    assert len(human.actors.now()) == 0


def test_human_define():
    model = MainModel()
    human = model.human
    farmers = human.agents.create(Farmer, 5)
    admins = model.agents.create(Admin, 5)

    farmers.update("test", np.arange(5))
    admins.update("test", np.arange(5))

    human.define("test", "Farmer")
    assert human.test == farmers
    human.agents.remove(farmers[0])
    assert human.test == farmers[1:]


def test_human_rule():
    model = MainModel()
    layer = PatchModule.from_resolution(model)
    human = model.human
    farmers = human.agents.create(Farmer, 5)
    farmers.trigger(
        "put_on_layer",
        layer=layer,
        pos=(2, 3),
    )

    farmers.trigger("rule", when="test == 1", then="die", disposable=True)
    # assert checked
    farmers.update("test", np.arange(5))
    assert human.agents.to_list().on_earth.sum() == 4
    farmers.trigger("rule", when="test == 2", then="die")
    assert len(human.agents) == 3
