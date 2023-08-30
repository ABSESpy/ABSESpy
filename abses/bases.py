#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/
from __future__ import annotations

import logging
from abc import ABCMeta, abstractmethod
from typing import Iterable, List, Optional, Set, Union

from agentpy.objects import make_list

logger = logging.getLogger(__name__)


class Creator:
    def __init__(self):
        self.created: List[Creation] = []
        self._inheritance: List[str] = []

    def _check_creation(self, creation: Creation):
        if not issubclass(creation.__class__, Creation):
            raise TypeError(
                f"Only creation can be added, input {creation.__class__}."
            )

    @property
    def inheritance(self) -> list:
        return self._inheritance

    @inheritance.setter
    def inheritance(self, attrs: "List[str]|str") -> None:
        self.inheritance.extend(make_list(attrs))
        self.notify()

    def add_creation(self, obj: Creation):
        self._check_creation(creation=obj)
        self.created.append(obj)
        setattr(obj, "_creator", self)
        self.notify()

    def notify(self):
        for obj in self.created:
            obj.refresh(self)

    def remove_creation(self, obj: Creation):
        self._check_creation(creation=obj)
        self.created.remove(obj)


class Creation(metaclass=ABCMeta):
    @property
    def creator(self):
        return self._creator

    def refresh(self, creator: Creator):
        for attr in creator.inheritance:
            value = creator.__getattribute__(attr)
            self.__setattr__(attr, value)


class Notice:
    """通知模块，全局变量会被实时更新给观察者"""

    __glob_vars__: Set[str] = []

    def __init__(self, observer: Optional[Observer] = None):
        self.observers: Set[Observer] = set()
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

    def attach(self, observer: Observer) -> None:
        """添加一个观察者"""
        self.observers.add(observer)
        observer.notification(self)

    def detach(self, observer: Observer) -> None:
        """移除一个观察者"""
        self.observers.remove(observer)

    def notify(self) -> None:
        """将特定变量通知给观察者"""
        for observer in self.observers:
            observer.notification(self)


class Observer(metaclass=ABCMeta):
    """观察者，模型全局变量变化的时候，会自动变化"""

    def notification(self, notice: Notice):
        """每当全局变量变化的时候，收到通知"""
        for var in notice.glob_vars:
            value = getattr(notice, var)
            setattr(self, var, value)


class Mediator:
    @abstractmethod
    def transfer_event(self, sender: object, event: str):
        pass

    @abstractmethod
    def transfer_parsing(self, sender: object, params: dict):
        pass

    @abstractmethod
    def transfer_request(self, sender: object, request: str):
        return request
