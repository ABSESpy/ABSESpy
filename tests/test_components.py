#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
测试模型的基本组件
"""

from abses.components import *


class MyComponent(Component):
    args = ["a", "b", "c"]

    def handle_params(self):
        self.handle = "handle is triggered"

    def initialize(self):
        self.init = "init is triggered, too"


class MyMainComp(MainComponent):
    pass


def test_component():
    comp = Component(name="comp1")
    comp.params = {"p1": 1}
    comp.arguments = "params"
    comp.arguments = ["a", "b", "a"]  # repeat 'a' will be removed

    assert comp.params.p1 == 1
    assert comp.params["p1"] == 1
    assert comp.arguments == ["a", "b", "params"]


def test_arguments():
    comp = MyComponent()
    comp.params = {
        "a": 1,
        "b": 2,
    }

    try:
        comp._parsing_args()
    except KeyError as e:
        assert "c" in e.__str__()
    assert comp.a == 1
    assert comp.b == 2
    assert "a" not in comp.params
    assert not hasattr(comp.params, "b")

    comp2 = MyMainComp()
    comp2.arguments = comp.arguments
    assert "a" in comp2.arguments
    assert "a" not in comp2.params
    try:
        comp2._parsing_args()
    except KeyError as e:
        assert "a" in e.__str__()


def test_parse_parameter():
    params = {
        "comp1": {"a": 1, "b": 2, "c": 3},
        "comp2": {"a": -1, "b": -2, "c": -3},
        "exist": "unsolved param",
    }
    comp1 = MyComponent(name="comp1")
    comp2 = MyMainComp(name="comp2")

    comp1.parsing_params(params)
    comp2.parsing_params(params)
    assert "comp1" not in params
    assert "comp2" not in params
    assert "exist" in params
    assert comp1.a == 1  # as argument
    assert "is triggered" in comp1.handle
    assert comp2.params.a == -1  # as a parameter
    assert not hasattr(comp2, "a")


def test_main_states():
    class TestMediator(Mediator):
        def transfer_event(self, sender: object, event: str):
            self.state = event

    comp = MyMainComp()
    mediator = comp.mediator = TestMediator()

    assert comp._state == -1
    assert comp.state == STATES[-1]

    # cannot setting wrong code:
    try:
        comp.state = -2
    except ValueError as e:
        assert "Invalid state" in e.__str__()
        assert f"{STATES}" in e.__str__()

    # cannot setting repeat code:
    try:
        comp.state = -1
    except ValueError as e:
        assert "repeat" in e.__str__()

    # correct setting:
    comp.state = 0
    assert mediator.state == comp.state == STATES[0]

    # cannot setting lower code
    comp.state = 1
    assert mediator.state == comp.state == STATES[1]
    comp.state = 2
    assert mediator.state == comp.state == STATES[2]

    try:
        comp.state = 1
    except ValueError as e:
        assert "retreat" in e.__str__()
