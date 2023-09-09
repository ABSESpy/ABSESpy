#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .objects import BaseObj


class DynamicVariable:
    """根据时间自动更新的数据"""

    def __init__(self, name, obj, data, function) -> None:
        self._name = name
        self._obj = obj
        self._data = data
        self._function = function

    @property
    def name(self):
        """变量名称"""
        return self._name

    @property
    def obj(self):
        """所属模块"""
        return self._obj

    @obj.setter
    def obj(self, obj: BaseObj):
        if not isinstance(obj, BaseObj):
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

    def now(self) -> Any:
        """当前值"""
        return self.function(
            obj=self.obj,
            data=self.data,
            time=self.time,
        )
