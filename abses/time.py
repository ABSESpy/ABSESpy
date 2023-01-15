#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

import threading
from collections import deque
from typing import Any, Deque, Dict, List, Optional, Union

from pandas import Period

from .bases import Notice
from .tools.func import wrap_opfunc_to
from .variable import MAXLENGTH, Variable


class TimeDriverManager:
    def __init__(self, period: Period, model: int) -> None:
        self._data: Period = period
        self._time: List[Period] = [period]
        self._history = deque([], maxlen=MAXLENGTH)
        self._model = model
        # instances operational func using the property '_data'
        wrap_opfunc_to(self, "_data")

    def __getattribute__(self, __name: str) -> Any:
        if __name.startswith("_"):
            return super().__getattribute__(__name)
        # using data explicit methods.
        elif hasattr(self._data, __name):
            return getattr(self._data, __name)
        else:
            TimeDriver._select_manager(self._model)
            return getattr(TimeDriver, __name)

    def __lt__(self, other):
        return self._data < other

    def __eq__(self, other):
        return self._data == other

    def __str__(self) -> str:
        start = self._time[0]
        end = self._time[-1]
        return f"[{self.freqstr}]{start}-{end}"

    def __repr__(self) -> str:
        return self._data.__str__()


class TimeDriver(Period):
    _manager: TimeDriverManager = None
    _model: Dict[int, TimeDriverManager] = {}
    _lock = threading.RLock()

    # 单例模式：https://www.jb51.net/article/202178.htm
    def __new__(cls, *args, **kwargs):
        """A Singleton Wrapper class, each model has its own driver."""
        model_id = kwargs.pop("model", 0)
        if cls._model.get(model_id) is None:
            period = Period(*args, **kwargs)
            driver = TimeDriverManager(period, model_id)
            with cls._lock:
                cls._model[model_id] = driver
        else:
            driver = cls._model[model_id]
        return driver

    @classmethod
    def _select_manager(cls, model):
        with cls._lock:
            cls._manager = cls._model[model]

    @classmethod
    def update(cls, steps: Optional[int] = 1) -> Period:
        for _ in range(steps):
            cls.history.append(cls.data)
            cls._manager._data = cls.data + 1
            cls.time.append(cls.data)
        return cls._manager._data

    @classmethod
    @property
    def history(cls):
        return cls._manager._history

    @classmethod
    @property
    def data(cls):
        return cls._manager._data

    @classmethod
    @property
    def time(cls):
        return cls._manager._time
