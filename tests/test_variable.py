#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import datetime

from abses import BaseObj
from abses.bases import Creation
from abses.main import MainModel
from abses.variable import Variable, VariablesRegistry

from .test_objects import noticeable_model


def create_variable(*args):
    for _, v in enumerate(args):
        var = Variable(v)
        yield var


def check_testing_string(string) -> bool:
    return "testing" in string


def test_variable_data():
    var1, var2, var3 = create_variable(0.1, 2, "defect")

    assert var1.__repr__() == "<[None]Var: 0.1>"
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
    assert var3.startswith("d")


# def test_variable_dtype():
#     var1, _, _, _ = create_variable(None, 1, "test", 0.1)
#     assert var1.dtype is None
#     var1.data = 1
#     assert var1.dtype == int
#     try:
#         var1.data = 0.1
#     except TypeError as e:
#         assert "mismatches" in str(e)
#     assert isinstance(var1, Creation)


def test_variable_registry():
    vr = VariablesRegistry(1)
    vr.register(owner=1, var_name="v1", dtype=type(0.1))
    vr.register(owner=1, var_name="v2", dtype=type(1))
    vr.register(owner=2, var_name="v2", dtype=type(1))
    vr.register(owner=2, var_name="v3", dtype=type("test"))
    assert vr.model == 1
    assert vr._variables == ["v1", "v2", "v3"]
    assert vr._objs_registry == {1: ["v1", "v2"], 2: ["v2", "v3"]}
    assert vr._map == {"v1": [1], "v2": [1, 2], "v3": [2]}
    assert vr._data_types == {"v1": float, "v2": int, "v3": str}
    assert vr._check_type("v1", float)
    assert vr._is_registered("v2")
    assert not vr._is_registered("v4")
    assert vr._has_variable(1, "v1")
    assert not vr._has_variable(2, "v1")
    assert vr.check_variable("v3", "testing")

    vr.delete_variable("v1")
    vr.delete_variable("v2", owner=2)
    vr.delete_variable("v3", owner=2)
    assert vr._variables == ["v2"]
    assert vr._objs_registry == {1: ["v2"]}
    assert vr._map == {"v2": [1]}
    assert vr._data_types == {"v2": int}
    assert vr._check_type("v2", int)
    assert vr._is_registered("v2")
    assert not vr._is_registered("v1")
    assert vr._has_variable(1, "v2")
    assert not vr._has_variable(2, "v1")
    assert vr[1] == ["v2"]


def test_variable_creation():
    model = noticeable_model()
    registry = VariablesRegistry(model)
    obj = BaseObj(model=model, observer=True)
    assert obj._registry is registry

    var = obj.register_a_var(
        name="test",
        init_data="testing var",
        long_name="a testing variable",
        check_func=[check_testing_string],
    )
    assert "testing" in var
    assert var + "!" == "testing var!"
    # var = obj.register_a_var(name="v1", long_name="Variable 1", init_data=1)
    # obj.add_creation(var)
    # t = datetime.datetime.now()
    # obj.time = t
    # obj.inheritance = "time"
    # assert var.time == t
    # assert obj.v1 is var
    # assert "v1" in obj.variables
    # obj.v1 = 2  # call var.update(2)
    # assert var == 2
    # var.data = 3
    # assert obj.v1 == 3
    # try:
    #     obj.v1 = 0.2
    # except TypeError as e:
    #     assert "mismatches" in str(e)


def test_variables_history():
    model = MainModel(name="test_variables_history", base="tests")
    model.human.register_a_var(
        "test",
        "testing",
        "test_variables_history",
        check_func=[check_testing_string],
    )
    assert "test" in model.human.vars
    model.time_go()
    assert model.human.test == "testing"
