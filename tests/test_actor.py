#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from abses.actor import Actor, check_rule, perception
from abses.sequences import ActorsList

from .create_tested_instances import Farmer, simple_main_model


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
    selection3 = "Actor"

    assert actor.selecting(selection=selection)
    assert actor.selecting(selection=selection2)
    assert actor.selecting(selection=selection3)

    actor2 = Farmer(model=model)

    actor2.test2 = 2
    actor2.test2 = "testing"
    assert actor2.selecting(selection=selection) is False
    assert actor2.selecting(selection=selection2) is False
    assert actor2.selecting(selection=selection3) is False


def test_actor_rule():
    model = simple_main_model(test_actor_rule)
    actor = Actor(model=model)
    assert actor.on_earth is False

    selection = {"test1": 1, "test2": "testing"}

    actor.rule(
        when=selection, then="settle_down", position=(3, 3), disposable=True
    )
    assert actor.selecting(selection) is False
    assert actor.on_earth is False

    actor.test1 = 1
    assert actor.selecting(selection) is False
    assert actor.on_earth is False

    actor.test2 = "testing"
    assert actor.selecting(selection) is True
    assert actor.on_earth is True
    assert actor.pos == (3, 3)


def test_actor_loop_rule():
    model = simple_main_model(test_actor_loop_rule)

    class MyActor(Actor):
        @perception
        def flag(self):
            return self.test < 3

        def testing(self):
            self.test += 1

        @check_rule(loop=True)
        def after_testing(self):
            self.passed = True

    actor = MyActor(model=model)
    actor.test = 0
    selection = {"flag": True}
    actor.rule(when=selection, then="testing", check_now=False)
    actor.after_testing()
    assert actor.test == 3
    assert actor.passed


def test_actor_request():
    model = simple_main_model(test_actor_request)
    actors = model.agents.create(Actor, 5)
    positions = [(4, 4), (4, 4), (4, 3), (5, 5), (5, 6)]
    model.nature.add_agents(actors, positions=positions)

    center = actors[0]
    assert center.pos == (4, 4)
    neighbors = center.request(
        "neighbors", header={"pos": center.pos}, receiver="nature"
    )
    assert type(neighbors) is ActorsList
    assert len(neighbors) == 2
    assert (neighbors.pos == [(4, 4), (4, 4)]).all()  # default distance = 0

    assert len(center.neighbors()) == 2
    assert (center.neighbors().pos == [(4, 3), (4, 4)]).all()
    # assert actors[0] in neighbors and actors[2] in neighbors
