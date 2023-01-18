#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from abses.modules import Module

from .create_tested_instances import simple_main_model

TO_RECORD = ["a", "b"]
TO_REPORT = ["b", "c"]


def test_modules_attributes():
    model = simple_main_model(test_modules_attributes)
    module = Module(model=model, name="tested_module")
    assert module.__repr__() == "<tested_module: open>"
    assert module.agents is model.agents
    module.switch_open_to(False)
    assert module.__repr__() == "<tested_module: closed>"


# def test_recording_variables():
#     pass
