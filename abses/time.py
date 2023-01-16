#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

import threading
from collections import deque
from typing import Any, Deque, Dict, List, Optional

from agentpy import Model
from pandas import Period

from .tools.func import wrap_opfunc_to
from .variable import MAXLENGTH


class TimeDriverManager:
    def __init__(self, period: Period, model: int) -> None:
        self._data: Period = period
        self._time: List[Period] = [period]
        self._history: Deque[Period] = deque([], maxlen=MAXLENGTH)
        self._model: Model = model
        # instances operational func using the property '_data'
        wrap_opfunc_to(self, "_data")

    def __getattribute__(self, __name: str) -> Any:
        # private attributes of TimeDriverManager
        if __name.startswith("_"):
            return super().__getattribute__(__name)
        # using data explicit methods.
        elif hasattr(self._data, __name):
            return getattr(self._data, __name)
        # accessible methods and attributes of TimeDriver
        else:
            TimeDriver._select_manager(self._model)
            return getattr(TimeDriver, __name)

    # cls(2000, 'Y') < Period(2001, 'Y')
    def __lt__(self, other):
        return self._data < other

    # cls(2000, 'Y') == Period(2000, 'Y')
    # cls(2000, 'Y') != Period(2000, 'M')
    def __eq__(self, other):
        return self._data == other

    def __str__(self) -> str:
        """[A-DEC]2000-2001"""
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
    def __new__(cls, *args, **kwargs) -> TimeDriverManager:
        """A Singleton wrapped class, each model has its own driver.
        This class has NO instance, but init a TimeDriverManager.
        Each model can only store one initialized TimeDriverManager instance.
        """
        model_id = kwargs.pop("model", 0)
        # if this is the first time to initialize.
        if cls._model.get(model_id) is None:
            period = Period(*args, **kwargs)
            driver = TimeDriverManager(period, model_id)
            with cls._lock:
                cls._model[model_id] = driver
        # if this model has a TimeDriverManager.
        else:
            driver = cls._model[model_id]
        return driver

    @classmethod
    def _select_manager(cls, model: int) -> None:
        """Switch to current model's manager."""
        with cls._lock:
            cls._manager = cls._model[model]

    @classmethod
    @property
    def period(cls) -> Period:
        return cls._manager._data

    @classmethod
    @property
    def history(cls) -> Deque[Period]:
        return cls._manager._history

    @classmethod
    @property
    def time(cls) -> List[Period]:
        return cls._manager._time

    @classmethod
    def update(cls, steps: Optional[int] = 1) -> Period:
        """
        Update the time period.

        Args:
            steps (Optional[int], optional): how many time steps to update. Defaults to 1.

        Returns:
            Period: after updating, the current time period.
        """
        for _ in range(steps):
            cls.history.append(cls.period)
            cls._manager._data = cls.period + 1
            cls.time.append(cls.period)
        return cls._manager._data
