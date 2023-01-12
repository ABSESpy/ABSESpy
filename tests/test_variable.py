#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/


from abses import MainModel
from abses.variable import Variable


def test_variable_data():
    model = MainModel()
    var1 = Variable(
        model=model, name="v1", long_name="variable 1", initial_value=0.1
    )  # float
    assert hasattr(var1, "__add__")
    var2 = Variable(
        model=model, name="v2", long_name="variable 2", initial_value=2
    )  # int
    var3 = Variable(
        model=model, name="v3", long_name="variable 3", initial_value="defect"
    )  # str
    assert var1 + 0.9 == 1.0
    assert var2 + 2 == 4
    assert var3 + "!" == "defect!"
