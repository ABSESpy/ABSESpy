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
from functools import total_ordering, wraps
from typing import TYPE_CHECKING, Optional, Union

from pandas import Period, Timestamp

from abses.components import Component

if TYPE_CHECKING:
    from .main import MainModel

DEFAULT_START = "2000-01-01 00:00:00"
DEFAULT_END = "2023-01-01 00:00:00"
DEFAULT_FREQ = "Y"
logger = logging.getLogger(__name__)


def time_condition(condition: dict, when_run: bool = True) -> callable:
    """
    A decorator to run a method based on a time condition.

    Parameters:
    - condition (dict): A dictionary containing conditions to check against the `time` attribute.
                        The keys can be ['year', 'month', 'weekday', 'freqstr'].
    - when_run (bool): If True, the decorated method will run when the condition is met.
                       If False, the decorated method will not run when the condition is met.

    Example usage:
    @time_condition(condition={'year': 2023, 'month': 9})
    def my_method(self):
        print("This method runs only if the `time` attribute is in September 2023.")
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, "time"):
                raise AttributeError("The `time` attribute must be existing.")
            time = self.time
            if not isinstance(time, TimeDriver):
                raise TypeError("The `TimeDriver` must be existing.")

            satisfied = all(
                getattr(time, key, None) == value
                for key, value in condition.items()
            )

            if (satisfied and when_run) or (not satisfied and not when_run):
                return func(self, *args, **kwargs)

        return wrapper

    return decorator


@total_ordering
class TimeDriver(Component):
    """TimeDriver provides the functionality to manage time."""

    _instances = {}
    _lock = threading.Lock()

    def __new__(cls, model: MainModel):
        with cls._lock:
            if not cls._instances.get(model):
                driver = super(TimeDriver, cls).__new__(cls)
                cls._instances[model] = driver
            else:
                driver = cls._instances[model]
        return driver

    def __init__(self, model: MainModel):
        super().__init__(model=model, name="time")
        self._model: MainModel = model
        self._current_period: Period = self.start_period
        self._history = deque([self.start_period])

    def __eq__(self, other: object) -> bool:
        return self.period.__eq__(other)

    def __lt__(self, other: object) -> bool:
        return self.period.__lt__(other)

    @property
    def freq(self) -> str:
        """The frequency of time"""
        freq = self.params.get("freq")
        if not freq:
            freq = DEFAULT_FREQ
            self.logger.warning(
                "Frequency is not set, using the default %s.", freq
            )
        return freq

    @property
    def start_period(self) -> Period:
        """The start period"""
        start = self.params.get("start")
        if not start:
            self.logger.warning(
                "Start time is not set, using the default %s.", start
            )
            start = DEFAULT_START
        return Period(start, freq=self.freq)

    @property
    def end_period(self) -> Period:
        """The start period"""
        end = self.params.get("end")
        if not end:
            self.logger.warning(
                "Ending time is not set, using the default %s.", end
            )
            end = DEFAULT_END
        return Period(end, freq=self.freq)

    @property
    def period(self) -> Period:
        """The current period"""
        return self._current_period

    def __repr__(self) -> str:
        return repr(self._current_period)

    def update(self, steps=1):
        """更新时间"""
        for _ in range(steps):
            new_period = self._current_period + 1
            if new_period > self.end_period:
                raise ValueError("Exceeding the end period")
            self._history.append(new_period)
            self._current_period = new_period

    @property
    def day(self) -> int:
        """当前是第几天"""
        return self.period.day

    @property
    def dayofweek(self) -> int:
        """当前是周几"""
        return self.period.dayofweek

    @property
    def dayofyear(self) -> int:
        """当前是年的第几天"""
        return self.period.dayofyear

    @property
    def daysinmonth(self) -> int:
        """当前月份的天数"""
        return self.period.daysinmonth

    @property
    def days_in_month(self) -> int:
        """目前是当前月份的第几天"""
        return self.period.days_in_month

    @property
    def end_time(self) -> Timestamp:
        """当前时间段的结束时间"""
        return self.period.end_time

    @property
    def hour(self) -> int:
        """当前是第几小时"""
        return self.period.hour

    @property
    def minute(self) -> int:
        """当前是第几分钟"""
        return self.period.minute

    @property
    def month(self) -> int:
        """当前月份"""
        return self.period.month

    @property
    def quarter(self) -> int:
        """当前季度"""
        return self.period.quarter

    @property
    def qyear(self) -> int:
        """当前是年的第几季度"""
        return self.period.qyear

    @property
    def second(self) -> int:
        """当前是第几秒"""
        return self.period.second

    @property
    def ordinal(self) -> int:
        """当前是年的第几周"""
        return self.period.ordinal

    @property
    def is_leap_year(self) -> bool:
        """是否是闰年"""
        return self.period.is_leap_year

    @property
    def start_time(self) -> Timestamp:
        """当前时间段的开始时间"""
        return self.period.start_time

    @property
    def week(self) -> int:
        """本年的第几周"""
        return self.period.week

    @property
    def weekday(self) -> int:
        """本年的第几周"""
        return self.period.weekday

    @property
    def weekofyear(self) -> int:
        """本年的第几周"""
        return self.period.weekofyear

    @property
    def year(self) -> int:
        """年份"""
        return self.period.year

    @property
    def day_of_year(self) -> int:
        """当前是年的第几天"""
        return self.period.day_of_year

    @property
    def day_of_week(self) -> int:
        """当前是周几"""
        return self.period.day_of_week

    def strftime(self, fmt: str) -> str:
        """转化成字符串时间"""
        return self.period.strftime(fmt)

    def to_timestamp(
        self, freq: Union[str, str] = None, how: Optional[str] = None
    ) -> Timestamp:
        """转化成时间点"""
        return self.period.to_timestamp(freq, how)
