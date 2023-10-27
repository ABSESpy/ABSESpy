#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from datetime import datetime

import pendulum
import pytest

from abses import MainModel
from abses.time import _TimeDriver


@pytest.fixture(name="default_time")
def set_default_time():
    """创建一个默认的时间模块"""
    model = MainModel()
    return _TimeDriver(model=model)


@pytest.fixture(name="yearly_time")
def set_year_time():
    """创建一个每次走一年的时间模块"""
    parameters = {
        "time": {
            "years": 1,
            "start": "2000",
            "end": "2020",
        }
    }
    model = MainModel(parameters=parameters)
    return model.time


def test_init_default_time(default_time: _TimeDriver):
    """测试初始化时间"""
    # 当前的时间
    assert default_time.dt.day == datetime.now().day
    assert default_time.dt.month == datetime.now().month
    assert default_time.dt.year == datetime.now().year
    # tick
    assert default_time.tick == 0
    assert default_time.start_dt == default_time.dt
    assert default_time.end_dt is None
    assert default_time.duration is None
    assert len(default_time.history) == 1
    assert default_time.history[0] == default_time.start_dt
    assert default_time.dt == default_time.start_dt
    assert default_time.ticking_mode == "tick"


def test_default_time_go(default_time: _TimeDriver):
    """测试默认时间的运行"""
    default_time.go()
    assert default_time.tick == 1
    assert default_time.dt == default_time.start_dt
    assert default_time.end_dt is None
    assert default_time.duration is None
    assert len(default_time.history) == 1


def test_different_model():
    """测试不同的模型使用不同的计数器"""
    model2 = MainModel(name="test_different_model_1")
    model3 = MainModel(name="test_different_model_2")
    time1 = _TimeDriver(model=model2)
    time2 = _TimeDriver(model=model3)
    # assert time1 == time2
    assert time1 is not time2
    time1.go()
    time2.go()
    assert time1 != time2


def test_init_yearly_time(yearly_time):
    """测试每年前进的模型的持续时间"""
    duration = pendulum.duration(years=1)

    assert yearly_time.tick == 0
    assert yearly_time.start_dt == pendulum.datetime(
        year=2000, month=1, day=1, tz=None
    )
    assert yearly_time.end_dt == pendulum.datetime(
        year=2020, month=1, day=1, tz=None
    )
    assert yearly_time.duration == duration
    assert len(yearly_time.history) == 1
    assert yearly_time.history[0] == yearly_time.start_dt

    yearly_time.go()
    assert yearly_time.tick == 1
    assert yearly_time.dt == pendulum.datetime(
        year=2001, month=1, day=1, tz=None
    )
    assert yearly_time.end_dt == pendulum.datetime(
        year=2020, month=1, day=1, tz=None
    )
    assert yearly_time.duration == duration
    assert len(yearly_time.history) == 2
