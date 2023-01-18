#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
测试对象
"""

from abses.actor import Actor
from abses.objects import BaseObj

from .create_tested_instances import noticeable_model


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

    class MyActor(Actor):
        pass

    class Father(MyActor):
        pass

    actor1 = MyActor(model=model, observer=True)
    actor2 = MyActor(model=model, observer=False)
    father = Father(model=model, observer=True)

    assert actor1.breed == actor2.breed == "myactor"
    assert father.breed == "father"
    assert actor1.a == 1
