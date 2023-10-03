#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from .objects import _BaseObj


class _DynamicVariable:
    """Time dependent variable

    A time dependent function will take the model time driver as
    an input and return its value. The function can also take other
    variables as inputs. The function can be defined as a static
    method of a class or a function.
    """

    def __init__(
        self, name: str, obj: _BaseObj, data: Any, function: Callable
    ) -> None:
        self._name: str = name
        self._obj: _BaseObj = obj
        self._data: Any = data
        self._function: Callable = function

    @property
    def name(self):
        """Get the name of the variable

        Returns
        -------
        name: str
        """
        return self._name

    @property
    def obj(self):
        """Returns a base object instance

        Returns
        -------
        obj: _BaseObj"""
        return self._obj

    @obj.setter
    def obj(self, obj: _BaseObj):
        if not isinstance(obj, _BaseObj):
            raise TypeError("Only accept observer object")
        self._obj = obj

    @property
    def data(self):
        """Returns unused data

        Returns
        -------
        data: Any
        """
        return self._data

    @property
    def function(self):
        """Get the function that calculates the variable

        Returns
        -------
        function: Callable
        """
        return self._function

    @property
    def time(self):
        """Get the model time driver

        Returns
        -------
        time: abses.time._TimeDriver"""
        return self.obj.time

    def get_required_attributes(self, function: Callable):
        """Get the function required attributes

        Returns
        -------
        required_attributes: list[str]"""
        # Get the source code of the function
        source_code = inspect.getsource(function)
        return [
            attr
            for attr in ["data", "obj", "time", "name"]
            if attr in source_code
        ]

    def now(self) -> Any:
        """Return the dynamic variable function's output

        Returns
        -------
        output: Any"""
        required_attrs = self.get_required_attributes(self.function)
        args = {attr: getattr(self, attr) for attr in required_attrs}
        return self.function(**args)
