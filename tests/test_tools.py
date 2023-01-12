#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from abses.tools.func import iter_func, warp_opfunc
from abses.tools.read_files import is_valid_yaml, read_yaml

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
