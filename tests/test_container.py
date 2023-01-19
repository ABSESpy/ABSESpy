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
    assert ac.__repr__() == "<AgentsContainer: (1)Farmer; (5)Admin>"
    assert ac.breeds == tuple(["Farmer", "Admin"])
    assert ac._breeds == {"Farmer": Farmer, "Admin": Admin}
    for admin in ac.Admin:
        assert admin in admins_5
    assert ac.Admin == admins_5

    # 增删
    another_farmer = Farmer(model)
    ac.add(another_farmer)
    ac.remove(admins_5[:2])
    assert ac.__repr__() == "<AgentsContainer: (2)Farmer; (3)Admin>"
