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

from abses.components import _Component

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
            if not isinstance(time, _TimeDriver):
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
class _TimeDriver(_Component):
    """TimeDriver provides the functionality to manage time.

    This class is responsible for managing the time of a simulation model. It keeps track of the current time period,
    updates it according to a given frequency, and provides properties to access different components of the current
    time period (e.g., day, hour, etc.). The `_TimeDriver` class is a singleton, meaning that there can be only one
    instance of it per simulation model. This is enforced by the `__new__` method, which returns an existing instance
    if it already exists for the given model, or creates a new one otherwise.

    Parameters
    ----------
    model : MainModel
        The simulation model that this time driver belongs to.

    Attributes
    ----------
    _instances : dict
        A dictionary that maps simulation models to their corresponding time drivers.
    _lock : threading.Lock
        A lock object to ensure thread safety when creating new instances of the `_TimeDriver` class.

    Methods
    -------
    freq() -> str
        Returns the time frequency of the time driver.
    start_period() -> Period
        Returns the starting time period for the model.
    end_period() -> Period
        Returns the final time period for the model.
    period() -> Period
        Returns the current time period for the model.
    update(steps=1) -> None
        Updates the current time period by a given number of steps.
    day() -> int
        Returns the current day for the model.
    dayofweek() -> int
        Returns the number for the day of the week for the model.
    dayofyear() -> int
        Returns the day of the year for the model.
    daysinmonth() -> int
        Returns the total number of days of the month that this period falls on for the model.
    days_in_month() -> int
        Returns the total number of days in the month that this period falls on for the model.
    end_time() -> Timestamp
        Returns the Timestamp for the end of the period.
    hour() -> int
        Returns the hour of the day component of the Period.
    minute() -> int
        Returns the minute of the hour component of the Period.
    """

    _instances = {}
    _lock = threading.Lock()

    def __new__(cls, model: MainModel):
        with cls._lock:
            if not cls._instances.get(model):
                driver = super(_TimeDriver, cls).__new__(cls)
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
        """Returns time frequency of the time driver.

        Returns
        -------
        freq : str
            Time frequency of the time driver.
        """
        freq = self.params.get("freq")
        if not freq:
            freq = DEFAULT_FREQ
            self.logger.warning(
                "Frequency is not set, using the default %s.", freq
            )
        return freq

    @property
    def start_period(self) -> Period:
        """Returns the starting time period for the model.

        Returns
        -------
        start_period : pandas.Period
            The starting time period for the model.
        """
        start = self.params.get("start")
        if not start:
            self.logger.warning(
                "Start time is not set, using the default %s.", start
            )
            start = DEFAULT_START
        return Period(start, freq=self.freq)

    @property
    def end_period(self) -> Period:
        """Returns the final time period for the model.

        Returns
        -------
        end_period : pandas.Period
            The final time period for the model.
        """
        end = self.params.get("end")
        if not end:
            self.logger.warning(
                "Ending time is not set, using the default %s.", end
            )
            end = DEFAULT_END
        return Period(end, freq=self.freq)

    @property
    def period(self) -> Period:
        """Returns the current time period for the model.

        Returns
        -------
        period : pandas.Period
            The current time period for the model.
        """
        return self._current_period

    def __repr__(self) -> str:
        return repr(self._current_period)

    def update(self, steps=1):
        """Updates model time by one step. The default.

        Parameters
        ----------
        steps : int, optional (default=1)
            The number of steps to update the model time.


        Returns
        -------
        None
        """
        for _ in range(steps):
            new_period = self._current_period + 1
            if new_period == self.end_period:
                self._model.running = False
            if new_period > self.end_period:
                raise ValueError("Exceeding the end period")
            self._history.append(new_period)
            self._current_period = new_period

    @property
    def day(self) -> int:
        """Returns the current day for the model.

        Returns
        -------
        day : int
            The day for the model.
        """
        return self.period.day

    @property
    def dayofweek(self) -> int:
        """Returns the number for the day of the week for the model.

        Returns
        -------
        dayofweek : int
            The day of the week for the model.
        """
        return self.period.dayofweek

    @property
    def dayofyear(self) -> int:
        """Returns the day of the year for the model.

        Returns
        -------
        dayofyear : int
            The day of the year for the model.
        """
        return self.period.dayofyear

    @property
    def daysinmonth(self) -> int:
        """Get the total number of days of the month that this period falls on for the model.

        Returns
        -------
        daysinmonth : int
            Days elapsed since the beginning of the month.
        """
        return self.period.daysinmonth

    @property
    def days_in_month(self) -> int:
        """Get the total number of days in the month that this period falls on for the model.

        Returns
        -------
        days_in_month : int
            Days in this months
        """
        return self.period.days_in_month

    @property
    def end_time(self) -> Timestamp:
        """Get the Timestamp for the end of the period.

        Returns
        -------
        end_time: pandas.Timestamp
            The Timestamp for the end of the period.
        """
        return self.period.end_time

    @property
    def hour(self) -> int:
        """Get the hour of the day component of the Period.

        Returns
        -------
        hour : int
            The hour of the day component of the Period.
        """
        return self.period.hour

    @property
    def minute(self) -> int:
        """Get minute of the hour component of the Period.

        Returns
        -------
        minute: int
            The minute of the hour component of the Period.
        """
        return self.period.minute

    @property
    def month(self) -> int:
        """Return the month the current model's Period falls on.

        Returns
        -------
        month: int
            The month the current model's Period falls on.
        """
        return self.period.month

    @property
    def quarter(self) -> int:
        """Return the quarter the current model's Period falls on.

        Returns
        -------
        quarter: int
            The quarter the current model's Period falls on.
        """
        return self.period.quarter

    @property
    def qyear(self) -> int:
        """Fiscal year a model's Period lies in according to its starting-quarter.

        Returns
        -------
        qyear: int
            The fiscal year a model's Period lies in according to its starting-quarter.
        """
        return self.period.qyear

    @property
    def second(self) -> int:
        """Get the second component of a model's Period.

        Returns
        -------
        second: int
            The second component of a model's Period.
        """
        return self.period.second

    @property
    def ordinal(self) -> int:
        """Returns period ordinal, which is the number of periods elapsed since a starting period.

        Returns
        -------
        ordinal : int
        """
        return self.period.ordinal

    @property
    def is_leap_year(self) -> bool:
        """Return True if the period's year is in a leap year.

        Returns
        -------
        is_leap_year : bool
        """
        return self.period.is_leap_year

    @property
    def start_time(self) -> Timestamp:
        """Get the Timestamp for the start of the period.

        Returns
        -------
        start_time : pandas.Timestamp"""
        return self.period.start_time

    @property
    def week(self) -> int:
        """Get the week of the year on the given Period.

        Returns
        -------
        week : int
        """
        return self.period.week

    @property
    def weekday(self) -> int:
        """Day of the week the period lies in, with Monday=0 and Sunday=6.

        Returns
        -------
        weekday : int
        """
        return self.period.weekday

    @property
    def weekofyear(self) -> int:
        """Get the week of the year on the given Period.

        Returns
        -------
        weekofyear : int
        """
        return self.period.weekofyear

    @property
    def year(self) -> int:
        """Return the year this Period falls on.

        Returns
        -------
        year : int
        """
        return self.period.year

    @property
    def day_of_year(self) -> int:
        """Return the day of the year.

        Returns
        -------
        day_of_year : int
        """
        return self.period.day_of_year

    @property
    def day_of_week(self) -> int:
        """Day of the week the period lies in, with Monday=0 and Sunday=6.

        Returns
        -------
        day_of_week : int
        """
        return self.period.day_of_week

    def strftime(self, fmt: str) -> str:
        """Returns a string representing the pandas.Period, controlled by an explicit format string."""
        return self.period.strftime(fmt)

    def to_timestamp(
        self, freq: Union[str, str] = None, how: Optional[str] = None
    ) -> Timestamp:
        """Returns the Timestamp representation of the pandas.Period"""
        return self.period.to_timestamp(freq, how)
