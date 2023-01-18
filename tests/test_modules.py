#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import pandas as pd

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


def test_recording_variables():
    model = simple_main_model(test_modules_attributes)
    module = Module(model=model, name="tested_module")

    module.a = 1
    module.b = 0.5
    module.c = "testing"

    module.params = {
        "open": True,
        "record": TO_RECORD,
        "report": TO_REPORT,
    }

    module._after_parsing()
    model.time_go(3)
    assert module.log == {"t": [0, 1, 2], "a": [1, 1, 1], "b": [0.5, 0.5, 0.5]}
    assert all(
        module.output.index == pd.period_range(start=2000, end=2002, freq="Y")
    )
