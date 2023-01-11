#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
测试模型的基本组件
"""

from abses.components import Component, MainComponent


def test_component():
    comp = Component(name="comp1")
    comp.params = {"p1": 1}
    comp.arguments = "params"
    comp.arguments = ["a", "b", "a"]  # repeat 'a' will be removed

    assert comp.params.p1 == 1
    assert comp.params["p1"] == 1
    assert comp.arguments == ["a", "b", "params"]


def test_arguments():
    class MyComponent(Component):
        args = ["a", "b", "c"]

        def handle_params(self):
            self.handle = "this will be triggered"

        def initialize(self):
            self.init = "this will be triggered, too"

    comp = MyComponent()
    comp.params = {
        "a": 1,
        "b": 2,
    }

    try:
        comp._init_arguments()
    except KeyError as e:
        assert "Argument c" in e.__str__()
    assert comp.a == 1
    assert comp.b == 2
    assert "a" not in comp.params
    assert not hasattr(comp.params, "b")


def test_broadcast():
    pass
