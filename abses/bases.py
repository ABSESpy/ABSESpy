#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
基础类实现了观察者模式。

让所有模型的更改能够实时分配给所有观察者。
"""

from __future__ import annotations

import logging
from abc import ABCMeta
from typing import List, Optional, Set, Union

from abses.tools.func import make_list

logger = logging.getLogger(__name__)


class _Notice:
    """通知模块，全局变量会被实时更新给观察者"""

    __glob_vars__: Set[str] = []

    def __init__(self, observer: Optional[_Observer] = None):
        self.observers: Set[_Observer] = set()
        self._glob_vars = set(self.__glob_vars__)
        if observer is not None:
            self.attach(observer)

    def __repr__(self) -> str:
        return (
            f"<Noticing {self.glob_vars} to {len(self.observers)} observers>"
        )

    @property
    def glob_vars(self) -> List[str]:
        """全局变量列表，其中的变量自动更新给所有的观察者"""
        return sorted(self._glob_vars)

    def add_glob_vars(self, value: Union[str, List[str]]):
        """添加新的全局变量"""
        new_vars = set(make_list(value))
        for var in new_vars:
            if not hasattr(self, var):
                raise AttributeError(
                    f"{var} is not a variable in {self.__class__}."
                )
            self._glob_vars.add(var)
        self.notify()

    def attach(self, observer: _Observer) -> None:
        """添加一个观察者"""
        self.observers.add(observer)
        observer.notification(self)

    def detach(self, observer: _Observer) -> None:
        """移除一个观察者"""
        self.observers.remove(observer)

    def notify(self) -> None:
        """将特定变量通知给观察者"""
        for observer in self.observers:
            observer.notification(self)


class _Observer(metaclass=ABCMeta):
    """观察者，模型全局变量变化的时候，会自动变化"""

    def notification(self, notice: _Notice):
        """每当全局变量变化的时候，收到通知"""
        for var in notice.glob_vars:
            value = getattr(notice, var)
            setattr(self, var, value)
