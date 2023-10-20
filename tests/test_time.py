#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import pytest
from omegaconf import DictConfig

from abses import MainModel
from abses.time import Period, _TimeDriver


def test_init_time():
    """测试初始化时间"""
    model = MainModel()
    p1 = Period(2000, freq="Y")
    p2 = Period(p1) + 1
    time = _TimeDriver(model=model)
    # time + 1  -> 2001
    time.update()
    assert time == p2 == time.period
    # Checking if the history is updated.
    time2 = _TimeDriver(model=model)  # time driver of the same model

    assert time2 is time
    with pytest.raises(ValueError):
        time.update(30)


def test_different_model():
    model2 = MainModel(name="test_different_model_1")
    model3 = MainModel(name="test_different_model_2")
    time1 = _TimeDriver(model=model2)
    assert time1.period == Period(2000, freq="Y")
    time2 = _TimeDriver(model=model3)
    # assert time1 == time2
    assert time1 is not time2
    time1.update(3)
    assert time1 == Period(2003, "Y")
    time2.update(4)
    assert time2 == Period(2004, "Y")
    assert time1 != time2


def test_time_settings():
    name = "test_different_model_4"
    params = {"time": {"start": "1998"}}
    model4 = MainModel(name=name, parameters=params)
    assert model4.settings.time.start == "1998"
    assert model4.settings.get("time") == DictConfig({"start": "1998"})
