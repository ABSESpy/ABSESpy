#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from typing import Any

from pandas import Period

from .bases import Notice
from .variable import Variable


class TimeVariable(Variable):
    def __init__(
        self,
        freq: str | None = ...,
        init_value: Period | str | None = ...,
    ):
        # https://pandas.pydata.org/docs/reference/api/pandas.Period.html
        init_period = Period(init_value, freq=freq)
        Variable.__init__(self, name="time", initial_value=init_period)
        self._periods = []
