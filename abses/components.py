#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
Components 是模型的基本组件，负责调度参数，让参数配置模块化。

用户在进行继承的时候，可以在类属性`__args__`中设定该模块必须的参数。
如果该参数在实验中没有被读取到，则会报错。

以下类继承了这个基本类：
1. 模型所有的模块
2. 主模型
3. TimeDriver 时间驱动器
4. DataCollector 数据收集器
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Iterable, Optional, Set, Union

from omegaconf import DictConfig

from abses.tools.func import make_list
from abses.tools.regex import MODULE_NAME

if TYPE_CHECKING:
    from abses.main import MainModel


class _Component:
    """
    Class _Component is used to represent a component of the model.
    Components are foundational pieces in constructing the model's entities.
    It is initialized with a model and a optional name.
    """

    __args__ = []

    def __init__(self, model: MainModel, name: Optional[str] = None):
        self._args: Set[str] = set()
        self._model: MainModel = model
        self.name: str = name
        self.add_args(self.__args__)

    @property
    def name(self) -> str:
        """Get the name of the component"""
        return self._name

    @name.setter
    def name(self, value: Optional[str]) -> None:
        """Set the name of the component"""
        if value is None:
            value = self.__class__.__name__.lower()
        if not isinstance(value, str):
            raise TypeError(f"Name must be a string, not {type(value)}.")
        if not re.match(MODULE_NAME, value):
            raise ValueError(f"Name '{value}' is not a valid name.")
        self._name = value

    @property
    def params(self) -> DictConfig:
        """Returns read-only model's parameters.

        Returns:
            dict:
                Dictionary of model's parameters.
        """
        return self._model.settings.get(self.name, DictConfig({}))

    @property
    def args(self) -> DictConfig:
        """Returns read-only component's arguments.

        Returns:
            DictConfig:
                Component's arguments dictionary.
        """
        return DictConfig({arg: self.params[arg] for arg in self._args})

    def add_args(self, args: Union[str, Iterable[str]]) -> None:
        """Add model's parameters as component's arguments.

        Parameters:
            args :
                Model's parameters to be added as component's arguments.
        """
        args_set = set(make_list(args))
        for arg in args_set:
            if arg not in self.params:
                raise KeyError(f"Argument {arg} not found.")
            self._args.add(arg)
