#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Optional, Set, Union

from omegaconf import DictConfig

from .log import _Log
from .tools.func import make_list

if TYPE_CHECKING:
    from abses.main import MainModel


class _Component(_Log):
    """
    The Base Component provides the basic functionality of storing a mediator's
    instance inside component objects.
    """

    __args__ = []

    def __init__(self, model: MainModel, name: Optional[str] = None):
        _Log.__init__(self, name=name)
        self._args: Set[str] = set()
        self._model = model
        self.add_args(self.__args__)

    @property
    def params(self) -> dict:
        """本模块的参数"""
        return self._model.settings.get(self.name, DictConfig({}))

    @property
    def args(self) -> DictConfig:
        """必须包含的参数名"""
        return DictConfig({arg: self.params[arg] for arg in self._args})

    def add_args(self, args: Union[str, Iterable[str]]) -> None:
        """添加新的参数名"""
        args_set = set(make_list(args))
        for arg in args_set:
            if arg not in self.params:
                raise KeyError(f"Argument {arg} not found.")
            self._args.add(arg)
