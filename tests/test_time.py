#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/
import pandas._libs.tslibs.period as pd

from abses.time import Period, TimeDriver, TimeDriverManager


def test_init_time():
    p1 = Period(2000, freq="Y")
    p2 = Period(p1) + 1
    time = TimeDriver(2000, freq="Y", model=1)

    assert time._data == p1
    assert type(time._data) is Period
    # time + 1  -> 2001
    assert time.update() == p2
    assert time.data == p2
    assert time.data is TimeDriver.data
    assert time._data is TimeDriver.data
    assert time._data == p2
    assert type(time) is TimeDriverManager
    assert TimeDriver._manager is time
    assert time == p2
    # Checking if the history is updated.
    assert len(time._history) == 1
    assert len(time._time) == 2
    time2 = TimeDriver(model=1)  # time driver of the same model

    assert time2 is time
    assert time.asfreq("M") == p2.asfreq("M")
    assert str(time) == "[A-DEC]2000-2001"

    time.update(10)
    assert time == Period(2011, "Y")
    assert len(time2._history) == 5
    assert len(time2._time) == 12


def test_different_model():
    time1 = TimeDriver(2000, freq="Y", model=2)
    assert time1._model == 2
    assert time1.data == Period(2000, freq="Y")
    time2 = TimeDriver(2000, freq="Y", model=3)
    assert time2._model == 3
    assert time1 == time2 == Period(2000, "Y")
    assert time1 is not time2
    time1.update(3)
    assert time1 == Period(2003, "Y")
    time2.update(4)
    assert time2 == Period(2004, "Y")
    assert time1 != time2


# def test_periodic_time():
#     time = TimeVariable(freq="Y", init_value=2000)
#     p1 = pd.Period(2000, freq="Y")
#     assert time == p1
#     assert p1 + 1 == pd.Period(2001, freq="Y")
#     assert Period('2000-12', 'M') == time.asfreq('M')
