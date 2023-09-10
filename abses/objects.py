#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

import mesa

from abses.time import TimeDriver

from .bases import Observer
from .dynamic import DynamicVariable
from .log import Log

if TYPE_CHECKING:
    from abses.main import MainModel


class BaseObj(Observer, Log):
    """
    基础对象，所有可以被用户自定义的对象都应该继承此类，包括：
    自然模块，人类模块，子模块，主体。
    其特点是这些模块可以访问模型的全局变量、时间驱动器，以及有各种自定义变量。
    """

    def __init__(
        self,
        model: MainModel,
        observer: Optional[bool] = True,
        name: Optional[str] = None,
    ):
        Log.__init__(self, name=name)
        self.time = TimeDriver(model)
        if observer:
            model.attach(self)
        self._model = model
        self._dynamic_variables: Dict[str, DynamicVariable] = {}

    @property
    def model(self) -> MainModel:
        """对应的模型"""
        return self._model

    @property
    def dynamic_variables(self) -> Dict[str, Any]:
        """所有动态变量"""
        for k, v in self._dynamic_variables.items():
            return {k: v.now()}

    @model.setter
    def model(self, model: MainModel):
        if not isinstance(model, mesa.Model):
            raise TypeError("Model must be an instance of mesa.Model")
        self._model = model

    def add_dynamic_variable(
        self, name: str, data: Any, function: Callable
    ) -> None:
        """
        添加一个动态变量
        name: 变量名
        data: 变量读取数据的源
        function: 变量读取数据的函数
        """
        var = DynamicVariable(
            obj=self, name=name, data=data, function=function
        )
        self._dynamic_variables[name] = var

    def dynamic_var(self, attr_name: str) -> Any:
        """获取一个动态变量当前的值"""
        return self._dynamic_variables[attr_name].now()
