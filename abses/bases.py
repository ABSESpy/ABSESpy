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
    def __init__(self, observer: Optional[Observer] = None):
        self.observers: Set[Observer] = set()
        self._glob_vars: List[str] = []
        if observer is not None:
            self.attach(observer)

    def __repr__(self) -> str:
        return f"<{len(self.observers)} are observing: {self.glob_vars}>"

    @property
    def glob_vars(self) -> List[str]:
        return self._glob_vars

    @glob_vars.setter
    def glob_vars(self, value: "str|List[str]"):
        self._glob_vars.extend(make_list(value))
        self.notify()

    def attach(self, observer: Observer):
        self.observers.add(observer)
        observer.notification(self)

    def detach(self, observer: Observer):
        self.observers.remove(observer)

    def notify(self, *args: str):
        if args:
            for attr in args:
                val = getattr(self, attr)
                for observer in self.observers:
                    setattr(observer, attr, val)
            logger.info(f"send {args} to {self.observers}")
        for observer in self.observers:
            observer.notification(self)


class Observer(metaclass=ABCMeta):
    def notification(self, notice: Notice):
        self.glob_vars = notice.glob_vars
        for var in self.glob_vars:
            value = getattr(notice, var)
            setattr(self, var, value)

    @property
    def glob_vars(self) -> List[str]:
        return self._glob_vars

    @glob_vars.setter
    def glob_vars(self, value: Union[Iterable[str], str]) -> None:
        if not hasattr(self, "_glob_vars"):
            self._glob_vars = []
        self._glob_vars.extend(make_list(value))


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
