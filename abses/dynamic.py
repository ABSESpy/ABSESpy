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
    """根据时间自动更新的数据"""

    def __init__(
        self, name: str, obj: _BaseObj, data: Any, function: Callable
    ) -> None:
        self._name: str = name
        self._obj: _BaseObj = obj
        self._data: Any = data
        self._function: Callable = function

    @property
    def name(self):
        """变量名称"""
        return self._name

    @property
    def obj(self):
        """所属模块"""
        return self._obj

    @obj.setter
    def obj(self, obj: _BaseObj):
        if not isinstance(obj, _BaseObj):
            raise TypeError("Only accept observer object")
        self._obj = obj

    @property
    def data(self):
        """数据"""
        return self._data

    @property
    def function(self):
        """函数"""
        return self._function

    @property
    def time(self):
        """时间"""
        return self.obj.time

    def get_required_attributes(self, function: Callable):
        """获取计算变量所需的属性"""
        # Get the source code of the function
        source_code = inspect.getsource(function)
        return [
            attr
            for attr in ["data", "obj", "time", "name"]
            if attr in source_code
        ]

    def now(self) -> Any:
        """当前值"""
        required_attrs = self.get_required_attributes(self.function)
        args = {attr: getattr(self, attr) for attr in required_attrs}
        return self.function(**args)
