#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import logging
from abc import ABCMeta
from typing import List, Optional

from agentpy.objects import Object, make_list

logger = logging.getLogger(__name__)


class Creator:
    def __init__(self):
        self.created: List[Creation] = []
        self._inheritance: list = []

    @property
    def inheritance(self) -> list:
        return self._inheritance

    @inheritance.setter
    def inheritance(self, attrs: "List[str]|str") -> None:
        self.inheritance.extend(make_list(attrs))
        self.notify()

    def add_creation(self, obj: object):
        self.created.append(obj)
        setattr(obj, "creator", self)
        self.notify()

    def notify(self):
        for obj in self.created:
            obj.refresh(self)

    def remove_creation(self, obj: object):
        self.created.remove(obj)


class Creation:
    def refresh(self, creator: Creator):
        for attr in creator.inheritance:
            value = creator.__getattribute__(attr)
            self.__setattr__(attr, value)


class Notice:
    def __init__(self, observer: Optional[object] = None):
        self.observers: List[Observer] = []
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

    def attach(self, observer: object):
        self.observers.extend(make_list(observer))
        observer.notification(self)

    def detach(self, observer: object):
        self.observers.remove(observer)

    def notify(self, *args: str):
        if len(args) > 0:
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
    def glob_vars(self, value: List[str]):
        self._glob_vars = value


class BaseObj(Observer, Object):
    def __init__(self, model, observer=True):
        Object.__init__(self, model=model)
        self.glob_vars: List[str] = []
        if observer:
            model.attach(self)
