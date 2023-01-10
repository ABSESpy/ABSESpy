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

from abses.objects import (BaseAgent, BaseObj, Creation, Creator, Notice,
                           Observer)


def test_creator_creation():
    creator = Creator()
    product1 = Creation()
    product2 = Creation()
    bad_product = object()

    creator.add_creation(product1)
    creator.add_creation(product2)
    try:
        creator.add_creation(bad_product)
    except Exception as e:
        assert e.__str__() == "Only creation can be added."

    # add something to be inherited
    creator.a = 1
    creator.b = bad_product
    creator.c = "testing"
    creator.inheritance = "a"
    creator.inheritance = ["b", "c"]

    assert product1.a == product2.a == 1
    assert product1.b == product2.b == bad_product
    assert product1.c == product2.c == "testing"

    creator.remove_creation(product2)
    creator.a = 2
    creator.notify()
    assert product1.a == 2
    # because product is removed, attr stay unchanged.
    assert product2.a == 1


def noticeable_model():
    class MyModel(Model, Notice):
        def __init__(self):
            Model.__init__(self)
            Notice.__init__(self)

    model = MyModel()
    model.a = 1
    model.glob_vars = "a"
    return model


def test_observer():
    model = Notice()
    model.a = "global"
    model.b = "specific attr"
    model.glob_vars = ["a"]

    ob1 = Observer()
    ob2 = Observer()
    ob1.notification(model)
    model.attach(ob2)
    model.notify("b")

    assert ob1.a == ob2.a == "global"
    assert ob2.b == "specific attr"
    assert "a" in ob1.glob_vars
    assert "a" in ob2.glob_vars


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
