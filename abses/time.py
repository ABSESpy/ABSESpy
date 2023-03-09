#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

import logging
import threading
from collections import deque
from typing import TYPE_CHECKING, Any, Deque, Dict, List, Optional

from agentpy import AttrDict
from pandas import Period

from .tools.func import wrap_opfunc_to
from .variable import MAXLENGTH

if TYPE_CHECKING:
    from .main import MainModel

DEFAULT_START = "2000-01-01 00:00:00"
DEFAULT_END = "2023-01-01 00:00:00"
DEFAULT_FREQ = "Y"
logger = logging.getLogger(__name__)


def parsing_settings(
    settings: Dict[str, Any], key: str, defaults: Optional[str]
) -> Period:
    freq = settings.get("freq", DEFAULT_FREQ)
    values = settings.get(key, defaults)
    return (
        Period(freq=freq, **values)
        if isinstance(values, dict)
        else Period(value=values, freq=freq)
    )


class TimeDriverManager:
    def __init__(self, model: MainModel, start, end) -> None:
        self._start = start
        self._end = end
        self._data: Period = start
        self._time: List[Period] = [start]
        self._history: Deque[Period] = deque([], maxlen=MAXLENGTH)
        self._model: MainModel = model
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
    def __new__(
        cls, model: MainModel, settings: Dict[str, Any] = None
    ) -> TimeDriverManager:
        """A Singleton wrapped class, each model has its own driver.
        This class has NO instance, but init a TimeDriverManager.
        Each model can only store one initialized TimeDriverManager instance.
        """
        if settings is None:
            settings = AttrDict()
        # if this is the first time to initialize.
        if cls._model.get(model) is None:
            start = parsing_settings(
                settings, key="start", defaults=DEFAULT_START
            )
            end = parsing_settings(settings, key="end", defaults=DEFAULT_END)
            driver = TimeDriverManager(model, start, end)
            with cls._lock:
                cls._model[model] = driver
        # if this model has a TimeDriverManager.
        else:
            driver = cls._model[model]
        return driver

    @classmethod
    def _select_manager(cls, model: int) -> None:
        """Switch to current model's manager."""
        with cls._lock:
            cls.manager = cls._model[model]

    @classmethod
    @property
    def period(cls) -> Period:
        return cls.manager._data

    @classmethod
    @property
    def history(cls) -> Deque[Period]:
        return cls.manager._history

    @classmethod
    @property
    def time(cls) -> List[Period]:
        return cls.manager._time

    @classmethod
    @property
    def manager(cls) -> TimeDriverManager:
        return cls._manager

    @classmethod
    @property
    def settings(cls) -> Dict[str, Any]:
        return cls._manager._model.params.get("time", {})

    @classmethod
    @property
    def end(cls) -> str:
        return cls._manager._end

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
            cls.manager._data = cls.period + 1
            cls.time.append(cls.period)
        return cls.manager._data
