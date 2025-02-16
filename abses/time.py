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
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Union,
    cast,
)

import pendulum
from omegaconf import DictConfig
from pendulum.datetime import DateTime
from pendulum.duration import Duration

from abses._bases.components import _Component
from abses._bases.logging import log_session

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


def parse_datetime(dt) -> DateTime:
    """Parse a string into date time."""
    if isinstance(dt, datetime):
        return pendulum.instance(dt, tz=None)
    if isinstance(dt, str):
        return cast(DateTime, pendulum.parse(dt, tz=None))
    raise TypeError("Start time must be a datetime object or a string.")


def time_condition(condition: dict, when_run: bool = True) -> Callable:
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
                getattr(time.dt, key, None) == value for key, value in condition.items()
            )

            if (satisfied and when_run) or (not satisfied and not when_run):
                return func(self, *args, **kwargs)

        return wrapper

    return decorator


@total_ordering
class TimeDriver(_Component):
    """TimeDriver provides the functionality to manage time.

    A wrapper around datetime that adds simulation-specific functionality while
    providing access to all datetime attributes and methods.
    """

    _instances: Dict[MainModel[Any, Any], TimeDriver] = {}
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
        self._model = model
        self._tick = 0
        self._dt = datetime.now()
        self._start_dt = self._dt
        self._end_dt: Optional[Union[datetime, int]] = None
        self._history: deque[DateTime] = deque()
        self._irregular = False
        self._duration: Duration | None = None
        self._parse_time_settings()
        self._history.append(self._dt)
        self._logging_setup()

    def __getattr__(self, name: str):
        """Redirect all undefined attributes to the datetime object."""
        return getattr(self._dt, name)

    def __repr__(self) -> str:
        if self.ticking_mode == "tick":
            return f"<TimeDriver: tick[{self.tick}]>"
        if self.ticking_mode == "duration":
            return f"<TimeDriver: {self.strftime('%Y-%m-%d %H:%M:%S')}>"
        return (
            f"<TimeDriver: irregular[{self.tick}] {self.strftime('%Y-%m-%d %H:%M:%S')}>"
        )

    def __eq__(self, other) -> bool:
        if isinstance(other, (datetime, TimeDriver)):
            return self.dt == (other.dt if isinstance(other, TimeDriver) else other)
        return NotImplemented

    def __lt__(self, other) -> bool:
        if isinstance(other, (datetime, TimeDriver)):
            return self.dt < (other.dt if isinstance(other, TimeDriver) else other)
        return NotImplemented

    def __deepcopy__(self, memo):
        return self

    @property
    def fmt(self) -> str:
        """String format of datetime."""
        hms = ("hours", "minutes", "seconds")
        if any(getattr(self.duration, item, None) for item in hms):
            return r"%Y-%m-%d %H:%M:%S"
        return r"%Y-%m-%d"

    @property
    def expected_ticks(self) -> Optional[int]:
        """Returns the expected ticks."""
        # If the end_dt is an integer or None, return the end_dt
        if isinstance(self.end_dt, int) or self.end_dt is None:
            return self.end_dt
        # If the end_dt is a datetime object, calculate the expected ticks
        if isinstance(self.end_dt, datetime):
            if self.duration is None:
                raise RuntimeError("No duration settings.")
            duration = self.end_dt - self.dt
            duration_seconds = duration.total_seconds()
            step_seconds = self.duration.total_seconds()
            return int(duration_seconds / step_seconds)
        raise TypeError("End time must be an integer or a datetime object.")

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
        """Current time advancement mode"""
        if self._duration:
            return "duration"
        return "irregular" if self._irregular else "tick"

    @property
    def history(self) -> List[datetime]:
        """Returns the history of the time driver."""
        return list(self._history)

    def to(self, time: str | datetime) -> None:
        """Specific the current time."""
        if isinstance(time, str):
            time = datetime.strptime(time, "%Y")
        self.dt = time
        self._history.clear()
        self._history.append(self.dt)

    def go(self, ticks: int = 1, **kwargs) -> None:
        """Advance simulation time"""
        if ticks < 0:
            raise ValueError("Ticks cannot be negative")

        for _ in range(ticks):
            self._tick += 1

            if self.ticking_mode == "duration" and self._duration:
                self.dt += self._duration
                self._history.append(self.dt)
            elif self.ticking_mode == "irregular":
                delta = pendulum.duration(**kwargs)
                self.dt += delta
                self._history.append(self.dt)
            if self.should_end:
                self._model.running = False
                break

    def _parse_time_settings(self) -> None:
        """Setup the time driver."""
        # Parse the start time settings
        self.start_dt = self.params.get("start", None)

        # Parse the end time settings
        self.end_dt = self.params.get("end", None)

        # Parse the duration settings
        self.parse_duration(self.params)

        # Parse the irregular settings
        self.irregular: bool = self.params.get("irregular", False)

        self.dt = self.start_dt

    def _logging_setup(self) -> None:
        if self.ticking_mode == "duration":
            end = (
                self.end_dt.strftime(self.fmt)
                if isinstance(self.end_dt, datetime)
                else str(self.end_dt)
            )
            msg = (
                f"Ticking mode: {self.ticking_mode}\n"
                f"Start time: {self.start_dt.strftime(self.fmt)}\n"
                f"End time: {end}\n"
                f"Duration: {self.duration}\n"
            )
        else:
            msg = (
                f"Ticking mode: {self.ticking_mode}\n"
                f"Start time: {self.start_dt.strftime(self.fmt)}\n"
                f"End time: {self.end_dt}\n"
            )
        log_session(title="TimeDriver", msg=msg)

    @property
    def irregular(self) -> bool:
        """Returns the irregular mode of the time driver."""
        return self._irregular

    @irregular.setter
    def irregular(self, value: bool) -> None:
        """Set the irregular mode of the time driver."""
        if not isinstance(value, bool):
            raise TypeError("Irregular mode must be a boolean.")
        self._irregular = value

    @property
    def duration(self) -> Duration | None:
        """Returns the duration of the time driver."""
        return self._duration

    def parse_duration(self, duration: DictConfig) -> None:
        """Set the duration using pendulum.Duration.

        Args:
            duration: Duration configuration containing time units

        Raises:
            ValueError: If any time unit is negative
            KeyError: If any time unit is invalid
        """
        # 检查时间单位是否为负数
        for unit, value in duration.items():
            if not isinstance(value, int):
                continue
            if value < 0:
                raise ValueError(f"Time unit {unit} cannot be negative")

        # 构建有效的时间步长
        valid_dict = {
            attr: duration.get(attr, 0)
            for attr in VALID_DT_ATTRS
            if isinstance(duration.get(attr, 0), int)
        }

        if all(value == 0 for value in valid_dict.values()):
            self._duration = None
        else:
            self._duration = pendulum.duration(**valid_dict)

    @property
    def start_dt(self) -> DateTime:
        """Returns the starting time for the model."""
        return self._start_dt

    @start_dt.setter
    def start_dt(self, dt: Optional[Union[datetime, DateTime, str]]) -> None:
        """Set the starting time."""
        if dt is None:
            self._start_dt = pendulum.instance(datetime.now(), tz=None)
        else:
            self._start_dt = parse_datetime(dt)

    @property
    def end_dt(self) -> Optional[Union[datetime, int]]:
        """
        The real-world time or the ticks when the model should be end.

        If the end time is a datetime object, it will be converted to a DateTime object.
        If the end time is an integer, it will be interpreted as a number of ticks.
        """
        return self._end_dt

    @end_dt.setter
    def end_dt(self, dt: Optional[Union[datetime, DateTime, str]]) -> None:
        if isinstance(dt, int) and dt <= 0:
            raise ValueError("End time cannot be negative.")
        if isinstance(dt, int):
            self._end_dt = dt
        elif isinstance(dt, datetime):
            self._end_dt = pendulum.instance(dt, tz=None)
        elif dt is None:
            self._end_dt = None
        elif isinstance(dt, str):
            self._end_dt = cast(DateTime, pendulum.parse(dt, tz=None))
        else:
            raise TypeError("End time must be a datetime object or a string.")

    @property
    def dt(self) -> DateTime:
        """Current simulation time"""
        return self._dt

    @dt.setter
    def dt(self, value: datetime) -> None:
        if not isinstance(value, datetime):
            raise TypeError("dt must be a datetime object")
        self._dt = value
