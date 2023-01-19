#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/


import numpy as np

from abses.container import AgentsContainer

from .create_tested_instances import Actor, Admin, Farmer, simple_main_model


def test_container_attributes():
    model = simple_main_model(test_container_attributes)
    ac = AgentsContainer(model=model)
    assert model.agents is ac
    assert ac.__len__() == 0
    assert ac.__repr__() == "<AgentsContainer: >"
    assert ac._model is model
    a_farmer = ac.create(Farmer)
    admins_5 = ac.create(Admin, 5)
    assert isinstance(a_farmer, Actor)
    assert ac.__len__() == 6
    assert ac.__repr__() == "<AgentsContainer: (1)farmer; (5)admin>"
    assert ac.breeds == tuple(["farmer", "admin"])
    assert ac._breeds == {"farmer": Farmer, "admin": Admin}
    for admin in ac.admin:
        assert admin in admins_5
    assert ac.admin == admins_5

    # 增删
    another_farmer = Farmer(model)
    ac.add(another_farmer)
    ac.remove(admins_5[:2])
    assert ac.__repr__() == "<AgentsContainer: (2)farmer; (3)admin>"
