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
from typing import TYPE_CHECKING, Dict, List, Optional

import pendulum

from abses.components import _Component

if TYPE_CHECKING:
    from .main import MainModel


VALID_DT_ATTRS = (
    "years",
    "months",
    "weeks",
    "days",
    "hours",
    "minutes",
    "seconds",
)


def time_condition(condition: dict, when_run: bool = True) -> callable:
    """
    A decorator to run a method based on a time condition.

    Parameters:
        condition:
            A dictionary containing conditions to check against the `time` attribute.
            The keys can be ['year', 'month', 'weekday', 'freqstr'].
        when_run:
            If True, the decorated method will run when the condition is met.
            If False, the decorated method will not run when the condition is met.

    Example:
        ```
        class TestActor(Actor):
            @time_condition(condition={"month": 1, "day": 1}, when_run=True)
            def happy_new_year(self):
                print("Today is 1th, January, Happy new year!")


        parameters = {"time": {"start": "1996-12-24", "days": 1}}


        model = MainModel(parameters=parameters)
        agent = model.agents.new(TestActor, 1, singleton=True)

        for _ in range(10):
            print(f"Time now is {model.time}")
            model.time.go()
            agent.happy_new_year()
        ```
        It should be called again in the next year beginning (i.e., `1998-01-01`) if we run this model longer... It means, the function will be called when the condition is fully satisfied.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, "time"):
                raise AttributeError(
                    "The object doesn't have a TimeDriver object as `time` attribute."
                )
            time = self.time
            if not isinstance(time, TimeDriver):
                raise TypeError("The `TimeDriver` must be existing.")

            satisfied = all(
                getattr(time.dt, key, None) == value
                for key, value in condition.items()
            )

            if (satisfied and when_run) or (not satisfied and not when_run):
                return func(self, *args, **kwargs)

        return wrapper

    return decorator


@total_ordering
class TimeDriver(_Component):
    """TimeDriver provides the functionality to manage time.

    This class is responsible for managing the time of a simulation model. It keeps track of the current time period, updates it according to a given frequency, and provides properties to access different components of the current time period (e.g., day, hour, etc.). The `TimeDriver` class is a singleton, meaning that there can be only one instance of it per simulation model.

    When init a `TimeDriver`, it accepts below parameters:

    | Parameter Name | Expected Data Type | Default Value | Description |
    |----------------|--------------------|---------------|-------------|
    | start          | str, None                | None          | If None: use the current time, else: should be a string which can be parsed by `pendulum.parse()`. |
    | end            | str, int, None         | None          | If it's a string that can be parsed into datetime the model should end until achieving this time; if int: the model should end in that tick; if None no auto-end. |
    | irregular         | bool               | False         | If False: not dive into an irregular mode (tick-mode); if True, the model will solve as an irregular mode. |
    | years          | int                | 0             | Time duration in years for the duration mode. |
    | months         | int                | 0             | Time duration in months for the duration mode. |
    | weeks          | int                | 0             | Time duration in weeks for the duration mode. |
    | days           | int                | 0             | Time duration in days for the duration mode. |
    | hours          | int                | 0             | Time duration in hours for the duration mode. |
    | minutes        | int                | 0             | Time duration in minutes for the duration mode. |
    | seconds        | int                | 0             | Time duration in seconds for the duration mode. |

    See tutorial to see more.
    """

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
        self._tick: int = 0
        self._start_dt: Optional[datetime] = None
        self._duration: Optional[pendulum.duration] = None
        self._history = deque()
        self._parse_time_settings()

    def __repr__(self) -> str:
        if self.ticking_mode == "tick":
            return f"<TimeDriver: tick[{self.tick}]>"
        if self.ticking_mode == "duration":
            return f"<TimeDriver: {self.strftime('%Y-%m-%d %H:%M:%S')}>"
        return f"<TimeDriver: irregular[{self.tick}] {self.strftime('%Y-%m-%d %H:%M:%S')}>"

    def __eq__(self, other: object) -> bool:
        return self.dt.__eq__(other)

    def __lt__(self, other: object) -> bool:
        return self.dt.__lt__(other)

    @property
    def should_end(self) -> bool:
        """Should the model end or not."""
        if not self.end_dt:
            return False
        if isinstance(self.end_dt, datetime):
            return self.dt >= self.end_dt
        return self._tick >= self.end_dt

    @property
    def tick(self) -> int:
        """Returns the current tick."""
        return self._tick

    @property
    def ticking_mode(self) -> str:
        """Returns the ticking mode of the time driver."""
        if self.duration:
            return "duration"
        return "irregular" if self._irregular else "tick"

    @property
    def history(self) -> List[datetime]:
        """Returns the history of the time driver."""
        return list(self._history)

    def go(self, ticks: int = 1, **kwargs) -> None:
        """Increments the tick.

        Parameters:
            ticks:
                How many ticks to increase.
        """
        if ticks < 0:
            raise ValueError("Ticks cannot be negative.")
        if ticks == 0 and self.ticking_mode != "irregular":
            raise ValueError(
                "Ticks cannot be zero unless the ticking mode is 'irregular'."
            )
        if ticks > 1:
            for _ in range(ticks):
                self.go(ticks=1, **kwargs)
            return
        # tick = 1
        self._tick += ticks
        if self.ticking_mode == "duration":
            self.dt += self.duration
            self._history.append(self.dt)
        elif self.ticking_mode == "irregular":
            self.dt += pendulum.duration(**kwargs)
            self._history.append(self.dt)
        elif self.ticking_mode != "tick":
            raise ValueError(f"Invalid ticking mode: {self.ticking_mode}")
        # end going
        if self.should_end:
            self._model.running = False

    # def stdout(self) -> None:
    #     """Print the current time."""
    #     report = f"tick[{self.tick}] " + self.strftime("%Y-%m-%d %H:%M:%S")
    #     # logger.info(report)
    #     sys.stdout.write("\r" + report)
    #     sys.stdout.flush()

    def _parse_time_settings(self) -> None:
        """Setup the time driver."""
        # Parse the start time settings
        self.start_dt = self.params.get("start")
        # logger.debug(f"start_dt: {self.start_dt}")

        # Parse the end time settings
        self.end_dt = self.params.get("end")
        # logger.debug(f"end_dt: {self.end_dt}")

        # Parse the duration settings
        self.parse_duration(self.params)
        # logger.debug(f"duration: {self.duration}")

        # Parse the irregular settings
        self._irregular = self.params.get("irregular")
        # logger.debug("irregular: {}", self._irregular)
        # logger.debug("Ticking mode: {}", self.ticking_mode)

        self.dt = self.start_dt
        self._history.append(self.dt)

    @property
    def duration(self) -> pendulum.duration | None:
        """Returns the duration of the time driver."""
        return self._duration

    def parse_duration(self, duration: Dict[str, int]) -> None:
        """Set the duration of the time driver."""
        valid_attributes = VALID_DT_ATTRS
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
        """Returns the starting time for the model."""
        return self._start_dt

    @start_dt.setter
    def start_dt(self, dt: datetime | None) -> None:
        """Set the starting time."""
        if isinstance(dt, datetime):
            self._start_dt = pendulum.instance(dt, tz=None)
        elif dt is None:
            self._start_dt = pendulum.instance(datetime.now(), tz=None)
        elif isinstance(dt, str):
            self._start_dt = pendulum.parse(dt, tz=None)
        else:
            raise TypeError(
                "Start time must be a datetime object or a string."
            )

    @property
    def end_dt(self) -> datetime | int | None:
        """The real-world time or the ticks when the model should be end."""
        return self._end_dt

    @end_dt.setter
    def end_dt(self, dt: datetime | int | None) -> None:
        if isinstance(dt, int) and dt <= 0:
            raise ValueError("End time cannot be negative.")
        if isinstance(dt, int):
            self._end_dt = dt
        elif isinstance(dt, datetime):
            self._end_dt = pendulum.instance(dt, tz=None)
        elif dt is None:
            self._end_dt = None
        elif isinstance(dt, str):
            self._end_dt = pendulum.parse(dt, tz=None)
        else:
            raise TypeError("End time must be a datetime object or a string.")

    @property
    def dt(self) -> datetime:
        """The current real-world time for the model without timezone information."""
        return self._dt

    @dt.setter
    def dt(self, dt: datetime) -> None:
        """Set the current real-world time."""
        if not isinstance(dt, datetime):
            raise TypeError("dt must be a datetime object.")
        self._dt = dt

    @property
    def day(self) -> int:
        """Returns the current day for the model."""
        return self.dt.day

    @property
    def dayofweek(self) -> int:
        """Returns the number for the day of the week for the model."""
        return self.dt.dayofweek

    @property
    def dayofyear(self) -> int:
        """Returns the day of the year for the model."""
        return self.dt.dayofyear

    @property
    def daysinmonth(self) -> int:
        """Get the total number of days of the month that this period falls on for the model."""
        return self.dt.daysinmonth

    @property
    def days_in_month(self) -> int:
        """Get the total number of days in the month that this period falls on for the model."""
        return self.dt.days_in_month

    @property
    def hour(self) -> int:
        """Get the hour of the day component of the Period."""
        return self.dt.hour

    @property
    def minute(self) -> int:
        """Get minute of the hour component of the Period."""
        return self.dt.minute

    @property
    def month(self) -> int:
        """Return the month the current model's Period falls on."""
        return self.dt.month

    @property
    def quarter(self) -> int:
        """Return the quarter the current model's Period falls on."""
        return self.dt.quarter

    @property
    def qyear(self) -> int:
        """Fiscal year a model's Period lies in according to its starting-quarter."""
        return self.dt.qyear

    @property
    def second(self) -> int:
        """Get the second component of a model's Period."""
        return self.dt.second

    @property
    def ordinal(self) -> int:
        """Returns period ordinal, which is the number of periods elapsed since a starting period."""
        return self.dt.ordinal

    @property
    def is_leap_year(self) -> bool:
        """Return True if the period's year is in a leap year."""
        return self.dt.is_leap_year

    @property
    def week(self) -> int:
        """Get the week of the year on the given Period."""
        return self.dt.week

    @property
    def weekday(self) -> int:
        """Day of the week the period lies in, with Monday=0 and Sunday=6."""
        return self.dt.weekday

    @property
    def weekofyear(self) -> int:
        """Get the week of the year on the given Period."""
        return self.dt.weekofyear

    @property
    def year(self) -> int:
        """Return the year this Period falls on."""
        return self.dt.year

    @property
    def day_of_year(self) -> int:
        """Return the day of the year."""
        return self.dt.day_of_year

    @property
    def day_of_week(self) -> int:
        """Day of the week the period lies in, with Monday=0 and Sunday=6."""
        return self.dt.day_of_week

    def strftime(self, fmt: str) -> str:
        """Returns a string representing the current time.

        Parameters:
            fmt:
                An explicit format string of datetime.
        """
        return self.dt.strftime(fmt)
