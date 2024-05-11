#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""Dynamic variables
"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, Callable, List

if TYPE_CHECKING:
    from ..time import TimeDriver
    from .objects import _BaseObj


class _DynamicVariable:
    """Time dependent variable

    A time dependent function will take the model time driver as
    an input and return its value. The function can also take other
    variables as inputs. The function can be defined as a static
    method of a class or a function.
    """

    def __init__(
        self, name: str, obj: _BaseObj, data: Any, function: Callable, **kwargs
    ) -> None:
        self._name: str = name
        self._obj: _BaseObj = obj
        self._data: Any = data
        self._function: Callable = function
        self._cached_data: Any = None
        self.attrs = kwargs
        self.now()

    @property
    def name(self) -> str:
        """Get the name of the variable

        Returns
        -------
        name: str
        """
        return self._name

    @property
    def obj(self) -> _BaseObj:
        """Returns a base object instance

        Returns:
            obj:
                _BaseObj
        """
        return self._obj

    @obj.setter
    def obj(self, obj: _BaseObj):
        if not isinstance(obj, _BaseObj):
            raise TypeError("Only accept observer object")
        self._obj = obj

    @property
    def data(self) -> Any:
        """Returns unused data

        Returns:
            data:
                Any
        """
        return self._data

    @property
    def function(self) -> Callable:
        """Get the function that calculates the variable

        Returns:
            function:
                Callable
        """
        return self._function

    @property
    def time(self) -> TimeDriver:
        """Get the model time driver

        Returns:
            time:
                abses.time.TimeDriver
        """
        return self.obj.time

    def get_required_attributes(self, function: Callable) -> List[str]:
        """Get the function required attributes

        Returns:
            required_attributes:
                list[str]
        """
        # Get the source code of the function
        source_code = inspect.getsource(function)
        return [
            attr
            for attr in ["data", "obj", "time", "name"]
            if attr in source_code
        ]

    def now(self) -> Any:
        """Return the dynamic variable function's output

        Returns:
            The dynamic data value now.
        """
        required_attrs = self.get_required_attributes(self.function)
        args = {attr: getattr(self, attr) for attr in required_attrs}
        result = self.function(**args)
        self._cached_data = result
        return result

    @property
    def cache(self) -> Any:
        """Return the dynamic variable's cache"""
        return self._cached_data
