#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
测试对象
"""

from agentpy import Model

from abses.bases import Notice, Observer
from abses.objects import BaseAgent, BaseObj


def noticeable_model():
    class MyModel(Model, Notice):
        def __init__(self):
            Model.__init__(self)
            Notice.__init__(self)

    model = MyModel()
    model.a = 1
    model.glob_vars = "a"
    return model


def test_base_object():
    model = noticeable_model()
    obj1 = BaseObj(model, True)
    obj2 = BaseObj(model, False)
    # create then change attr

    assert obj1.a == 1
    assert "a" in obj1.glob_vars
    assert not hasattr(obj2, "a")
    # change attr then create object
    obj3 = BaseObj(model, True)
    assert obj3.a == 1
    assert "a" in obj3.glob_vars


def test_base_agent():
    model = noticeable_model()

    class Actor(BaseAgent):
        pass

    class Father(BaseAgent):
        pass

    actor1 = Actor(model=model, observer=True)
    actor2 = Actor(model=model, observer=False)
    father = Father(model=model, observer=True)

    assert actor1.breed == actor2.breed == "actor"
    assert father.breed == "father"
    assert actor1.a == 1
