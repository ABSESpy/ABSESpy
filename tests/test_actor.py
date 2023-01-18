#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from abses.actor import Actor

from .create_tested_instances import simple_main_model


def test_actor_attributes():
    model = simple_main_model(test_actor_attributes)
    actor = Actor(model=model)

    assert actor.mediator is model.mediator
    assert actor.on_earth is False
    assert actor.breed == "actor"
    pos = (3, 3)
    model.nature.add_agents(agents=[actor], positions=[pos])
    assert actor.on_earth is True
    assert actor.pos == pos
