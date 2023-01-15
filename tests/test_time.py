#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/


import pandas as pd

from abses.time import Period, TimeVariable


def test_periodic_time():
    time = TimeVariable(freq="Y", init_value=2000)
    p1 = pd.Period(2000, freq="Y")
    assert time == p1
    assert p1 + 1 == pd.Period(2001, freq="Y")
