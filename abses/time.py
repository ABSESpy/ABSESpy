#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

import threading
from collections import deque
from typing import Any, Deque, List, Optional, Union

from pandas import Period

from .bases import Notice
from .tools.func import wrap_opfunc_to
from .variable import MAXLENGTH, Variable


class TimeDriverManager:
    def __init__(self, period: Period) -> None:
        self._time = [period]
        self._data = period
        self._history = deque([], maxlen=MAXLENGTH)
        wrap_opfunc_to(self, "_data")

    def update(self, steps: Optional[int] = 1) -> TimeDriver:
        for _ in range(steps):
            self._history.append(self.data)
            self._data += 1
            self._time.append(self.data)
        return self.data

    def __getattribute__(self, __name: str) -> Any:
        if __name.startswith("_"):
            return super().__getattribute__(__name)
        # using data explicit methods.
        elif hasattr(self._data, __name):
            return getattr(self.data, __name)
        else:
            return super().__getattribute__(__name)

    def __lt__(self, other):
        return self.data < other

    def __eq__(self, other):
        return self.data == other

    def __str__(self) -> str:
        start = self._time[0]
        end = self._time[-1]
        return f"[{self.freqstr}]{start}-{end}"

    @property
    def data(self):
        return self._data


class TimeDriver(Period):
    _model = {}
    _lock = threading.RLock()

    # 单例模式：https://www.jb51.net/article/202178.htm
    def __new__(cls, *args, **kwargs):
        model = kwargs.pop("model")
        if cls._model.get(model) is None:
            period = Period(*args, **kwargs)
            tm = TimeDriverManager(period)
            tm._data: Period = period
            tm._time: List[Period] = [period]
            tm._history: Deque[Period] = deque([], maxlen=MAXLENGTH)
            with cls._lock:
                cls._model[model] = tm
        else:
            tm = cls._model.get(model)
        return tm
