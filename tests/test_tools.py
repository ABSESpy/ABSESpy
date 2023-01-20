#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from abses.tools.func import *
from abses.tools.read_files import *

CONFIG = r"config/testing.yaml"


def test_parse_yaml():
    params = read_yaml(CONFIG, nesting=False)
    params_all = read_yaml(CONFIG, nesting=True)
    assert is_valid_yaml(params["world"])
    assert is_valid_yaml(params["groundwater"]["world"])
    assert is_valid_yaml(params["groundwater"]["nesting"]["world"])
    assert isinstance(params["world"], str)
    assert isinstance(params_all["world"], dict)
    assert isinstance(params_all["groundwater"]["world"], dict)
    assert isinstance(params_all["groundwater"]["nesting"]["world"], dict)
    # testing parse a invalid yaml file path.
    try:
        is_valid_yaml("bad_file.yaml")
    except ValueError as e:
        assert "bad_file.yaml" in e.__str__()


def test_iter_function():
    class Test:
        def __init__(self):
            self.elements = []

        @iter_func("elements")
        def testing(self, word: str):
            self.foo = word

    class Element(object):
        def testing(self, word):
            self.foo = word
            self.check = f"{self.foo} added auto."

    main = Test()
    comp1 = Element()
    comp2 = Element()

    main.elements.extend([comp1, comp2])
    main.testing("hello")
    assert main.foo == comp1.foo == comp2.foo == "hello"
    assert comp2.check == comp1.check == "hello added auto."


def test_wrap_opfunc():
    class Calculation:
        def __init__(self):
            self.attr = 1

    cal = Calculation()

    try:
        cal + 1
    except TypeError as e:
        assert "unsupported operand type(s)" in e.__str__()

    # wraping the '__add__' method.
    opname = "__add__"
    wrapper = opfunc_using_attr("attr", binary_op=True)
    wrapped_func = wrapper(getattr(1, opname))
    setattr(cal.__class__, opname, wrapped_func)
    assert cal + 1 == 2

    cal2 = Calculation()
    success = wrap_opfunc_to(cal2, "attr")
    assert "add" in success
    assert "radd" in success
    assert cal2 + 1 == 1 + cal2 == 2

    class MyClass(object):
        def __init__(self, attr: any):
            self.attr: any = attr

    int_obj = MyClass(1)
    str_obj = MyClass("test")
    float_obj = MyClass(0.1)

    opfunc_int = wrap_opfunc_to(int_obj, "attr")
    assert "mul" in opfunc_int
    assert "mod" in opfunc_int
    assert "pow" in opfunc_int
    assert int_obj + 1 == 1 + int_obj == 2
    wrap_opfunc_to(str_obj, "attr")
    assert str_obj * 2 == "testtest"
    wrap_opfunc_to(float_obj, "attr")
    assert float_obj * 10 == 1.0


def test_random_choosers():
    p = [0.0, -1.0, -1.0, -1.0]
    p2 = [300.0, -1.0, -1.0, -1]
    # possible entries == 0, p = None
    norm_choice(a=np.arange(4), size=2, p=p, replace=True)
    norm_choice(a=np.arange(4), size=2, p=None, replace=False)
    r3 = norm_choice(a=np.arange(4), size=2, p=p2, replace=True)
    r4 = norm_choice(a=np.arange(4), size=2, p=p2, replace=False)
    assert (np.array([0.0, 0.0]) == r3).all()
    assert 0 in r4
