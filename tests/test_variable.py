#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/


from abses import MainModel
from abses.variable import Variable


def test_variable_data():
    model = MainModel(base="tests")
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

    assert var1.dtype == float
    assert var2.dtype == int
    assert var3.dtype == str
    assert var1.__repr__() == "<Var[v1]: 0.1>"
    # --------------------------------
    # testing var ±*/ other -> var.data ±*/ other
    assert var1 + 0.9 == 1.0 == 0.9 + var1
    assert var1 - 0.1 == 0.0 == -(0.1 - var1)
    assert var2 - 1 == 1 == -(1 - var2)
    assert var2 + 2 == 4 == 2 + var2
    assert var3 + "!" == "defect!"
    assert var2**3 == 8
    assert var2 // 3 == 0
    assert var2 % 1 == 0
    assert -var1 == -0.1
    assert +var2 == 2
    assert var1 < 1
    assert 3 > var2
    # --------------------------------
    # assert var calculate with var
    assert var1 != var2
    assert var3 * var2 == "defectdefect"
    assert var2 > var1
    assert var1 <= var2
