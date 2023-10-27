#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

import threading
from collections import deque
from datetime import datetime
from functools import total_ordering, wraps
from typing import TYPE_CHECKING, Dict, List, Optional, Union

import pandas as pd
import pendulum
from loguru import logger

from abses.components import _Component

if TYPE_CHECKING:
    from .main import MainModel

DEFAULT_START = "2000-01-01 00:00:00"
DEFAULT_END = "2023-01-01 00:00:00"
DEFAULT_FREQ = "Y"


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


# @total_ordering
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
        self._tick: int = 0
        self._start_dt: Optional[datetime] = None
        self._duration: Optional[pendulum.duration] = None
        self._history = deque()
        self._parse_time_settings()

    def __repr__(self) -> str:
        return repr(self.dt)

    @property
    def tick(self) -> int:
        """Returns the current tick."""
        return self._tick

    @property
    def ticking_mode(self) -> str:
        """Returns the ticking mode of the time driver."""
        if self.duration:
            return "duration"
        return "now" if self._record else "tick"

    @property
    def history(self) -> List[datetime]:
        """Returns the history of the time driver."""
        return list(self._history)

    def go(self) -> None:
        """Increments the tick."""
        self._tick += 1
        if self.ticking_mode == "duration":
            self.dt += self.duration
            self._history.append(self.dt)
        elif self.ticking_mode == "now":
            self.dt = pendulum.now()
            self._history.append(self.dt)
        elif self.ticking_mode != "tick":
            raise ValueError(f"Invalid ticking mode: {self.ticking_mode}")

    def _parse_time_settings(self) -> None:
        """Setup the time driver."""
        # Parse the start time settings
        self.start_dt = self.params.get("start")
        logger.debug(f"start_dt: {self.start_dt}")

        # Parse the end time settings
        self.end_dt = self.params.get("end")
        logger.debug(f"end_dt: {self.end_dt}")

        # Parse the duration settings
        self.parse_duration(self.params)
        logger.debug(f"duration: {self.duration}")

        # Parse the record settings
        self._record = self.params.get("record")
        logger.debug("record: {}", self._record)
        logger.debug("Ticking mode: {}", self.ticking_mode)

        self.dt = self.start_dt
        self._history.append(self.dt)

    @property
    def duration(self) -> pendulum.duration | None:
        """Returns the duration of the time driver."""
        return self._duration

    def parse_duration(self, duration: Dict[str, int]) -> None:
        """Set the duration of the time driver."""
        valid_attributes = (
            "years",
            "months",
            "weeks",
            "days",
            "hours",
            "minutes",
            "seconds",
        )
        valid_dict = {}
        for attribute in valid_attributes:
            value = duration.get(attribute, 0)
            if not isinstance(value, int):
                raise TypeError(f"{attribute} must be an integer.")
            valid_dict[attribute] = value
        if all(value == 0 for value in valid_dict.values()):
            self._duration = None
        else:
            self._duration = pendulum.duration(**valid_dict)

    @property
    def start_dt(self) -> datetime | None:
        """Returns the starting time for the model.

        Returns
        -------
        start_period : pandas.Period
            The starting time period for the model.
        """
        return self._start_dt

    @start_dt.setter
    def start_dt(self, dt: datetime | None) -> None:
        """Set the starting time."""
        if isinstance(dt, datetime):
            self._start_dt = dt
        elif dt is None:
            self._start_dt = pendulum.now()
        elif isinstance(dt, str):
            self._start_dt = pendulum.parse(dt)
        else:
            raise TypeError(
                "Start time must be a datetime object or a string."
            )

    @property
    def end_dt(self) -> datetime | None:
        """Returns the final time for the model."""
        return self._end_dt

    @end_dt.setter
    def end_dt(self, dt: datetime | None) -> None:
        """Get the Timestamp for the end of the period.

        Returns
        -------
        end_time: pandas.Timestamp
            The Timestamp for the end of the period.
        """
        if isinstance(dt, datetime):
            self._end_dt = dt
        elif dt is None:
            self._end_dt = None
        elif isinstance(dt, str):
            self._end_dt = pendulum.parse(dt)
        else:
            raise TypeError("End time must be a datetime object or a string.")

    @property
    def dt(self) -> datetime:
        """Returns the current time period for the model.

        Returns
        -------
        period : pendulum.datetime
            The current real-world time for the model.
        """
        return self._dt

    @dt.setter
    def dt(self, dt: datetime) -> None:
        """Set the current real-world time."""
        if not isinstance(dt, datetime):
            raise TypeError("dt must be a datetime object.")
        self._dt = dt

    @property
    def day(self) -> int:
        """Returns the current day for the model.

        Returns
        -------
        day : int
            The day for the model.
        """
        return self.dt.day

    @property
    def dayofweek(self) -> int:
        """Returns the number for the day of the week for the model.

        Returns
        -------
        dayofweek : int
            The day of the week for the model.
        """
        return self.dt.dayofweek

    @property
    def dayofyear(self) -> int:
        """Returns the day of the year for the model.

        Returns
        -------
        dayofyear : int
            The day of the year for the model.
        """
        return self.dt.dayofyear

    @property
    def daysinmonth(self) -> int:
        """Get the total number of days of the month that this period falls on for the model.

        Returns
        -------
        daysinmonth : int
            Days elapsed since the beginning of the month.
        """
        return self.dt.daysinmonth

    @property
    def days_in_month(self) -> int:
        """Get the total number of days in the month that this period falls on for the model.

        Returns
        -------
        days_in_month : int
            Days in this months
        """
        return self.dt.days_in_month

    @property
    def hour(self) -> int:
        """Get the hour of the day component of the Period.

        Returns
        -------
        hour : int
            The hour of the day component of the Period.
        """
        return self.dt.hour

    @property
    def minute(self) -> int:
        """Get minute of the hour component of the Period.

        Returns
        -------
        minute: int
            The minute of the hour component of the Period.
        """
        return self.dt.minute

    @property
    def month(self) -> int:
        """Return the month the current model's Period falls on.

        Returns
        -------
        month: int
            The month the current model's Period falls on.
        """
        return self.dt.month

    @property
    def quarter(self) -> int:
        """Return the quarter the current model's Period falls on.

        Returns
        -------
        quarter: int
            The quarter the current model's Period falls on.
        """
        return self.dt.quarter

    @property
    def qyear(self) -> int:
        """Fiscal year a model's Period lies in according to its starting-quarter.

        Returns
        -------
        qyear: int
            The fiscal year a model's Period lies in according to its starting-quarter.
        """
        return self.dt.qyear

    @property
    def second(self) -> int:
        """Get the second component of a model's Period.

        Returns
        -------
        second: int
            The second component of a model's Period.
        """
        return self.dt.second

    @property
    def ordinal(self) -> int:
        """Returns period ordinal, which is the number of periods elapsed since a starting period.

        Returns
        -------
        ordinal : int
        """
        return self.dt.ordinal

    @property
    def is_leap_year(self) -> bool:
        """Return True if the period's year is in a leap year.

        Returns
        -------
        is_leap_year : bool
        """
        return self.dt.is_leap_year

    @property
    def start_time(self) -> datetime:
        """Get the Timestamp for the start of the period.

        Returns
        -------
        start_time : pandas.Timestamp"""
        return self.dt.start_time

    @property
    def week(self) -> int:
        """Get the week of the year on the given Period.

        Returns
        -------
        week : int
        """
        return self.dt.week

    @property
    def weekday(self) -> int:
        """Day of the week the period lies in, with Monday=0 and Sunday=6.

        Returns
        -------
        weekday : int
        """
        return self.dt.weekday

    @property
    def weekofyear(self) -> int:
        """Get the week of the year on the given Period.

        Returns
        -------
        weekofyear : int
        """
        return self.dt.weekofyear

    @property
    def year(self) -> int:
        """Return the year this Period falls on.

        Returns
        -------
        year : int
        """
        return self.dt.year

    @property
    def day_of_year(self) -> int:
        """Return the day of the year.

        Returns
        -------
        day_of_year : int
        """
        return self.dt.day_of_year

    @property
    def day_of_week(self) -> int:
        """Day of the week the period lies in, with Monday=0 and Sunday=6.

        Returns
        -------
        day_of_week : int
        """
        return self.dt.day_of_week

    def strftime(self, fmt: str) -> str:
        """Returns a string representing the pandas.Period, controlled by an explicit format string."""
        return self.dt.strftime(fmt)

    def to_timestamp(
        self, freq: Union[str, str] = None, how: Optional[str] = None
    ) -> datetime:
        """Returns the Timestamp representation of the pandas.Period"""
        return self.dt.to_timestamp(freq, how)
