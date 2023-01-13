#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from abses.bases import Creation, Creator, Notice, Observer


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
        assert "Only creation can be added" in e.__str__()

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
