#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/


from abses import MainModel

from .fixtures import Actor, Admin, Farmer


def test_container_attributes():
    """测试容器的属性"""
    model = MainModel()
    container = model.agents
    assert model.agents is container
    assert len(container) == 0
    assert repr(container) == "<AgentsContainer: >"
    assert container.model is model
    a_farmer = container.create(Farmer, singleton=True)
    admins_5 = container.create(Admin, 5)
    assert isinstance(a_farmer, Actor)
    assert len(container) == 6
    assert repr(container) == "<AgentsContainer: (1)Farmer; (5)Admin>"
    assert container.Admin == admins_5

    # 增删
    another_farmer = Farmer(model)
    assert "Farmer" in container.keys()
    container.add(another_farmer)
    container.remove(admins_5[0])
    admins_5[1:3].trigger("die")
    assert repr(container) == "<AgentsContainer: (2)Farmer; (2)Admin>"
