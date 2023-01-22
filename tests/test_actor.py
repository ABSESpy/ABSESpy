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
    assert actor.breed == "Actor"
    pos = (3, 3)
    model.nature.add_agents(agents=[actor], positions=[pos])
    assert actor.on_earth is True
    assert actor.pos == pos


def test_actor_selecting():
    model = simple_main_model(test_actor_selecting)
    actor = Actor(model=model)

    actor.test1 = 1
    actor.test2 = "testing"
    selection = {"test1": 1, "test2": "testing"}
    selection2 = "test1 == 1, test2 == testing"
    selection3 = "actor"

    assert actor.selecting(selection=selection)
    assert actor.selecting(selection=selection2)
    assert actor.selecting(selection=selection3)


def test_actor_rule():
    model = simple_main_model(test_actor_selecting)
    actor = Actor(model=model)
    assert actor.on_earth is False

    selection = {"test1": 1, "test2": "testing"}

    actor.rule(selection, "settle_down", None, (3, 3))
    expected = ("rule (1)", selection, "settle_down", ((3, 3),), {})
    for actual, expected in zip(actor._rules[0], expected):
        assert actual == expected
    assert actor.selecting(selection) is False
    assert actor.on_earth is False

    actor.test1 = 1
    assert actor.selecting(selection) is False
    assert actor.on_earth is False

    actor.test2 = "testing"
    assert actor.selecting(selection) is True
    assert actor.on_earth is True
    assert actor.pos == (3, 3)
