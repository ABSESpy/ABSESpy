#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
基础类实现了观察者模式。

让所有模型的更改能够实时分配给所有观察者。

The base class implements the observer pattern.
It allows to observe all attribute changes in the main model.
"""

from __future__ import annotations

import logging
from abc import ABCMeta
from typing import List, Optional, Set, Union

from abses.tools.func import make_list

logger = logging.getLogger(__name__)


class _Notice:
    """Notice class for the observer pattern."""

    __glob_vars__: Set[str] = set()

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
        """
        The global variable list, where the variables are automatically updated to all observers.
        """
        return sorted(self._glob_vars)

    def add_glob_vars(self, value: Union[str, List[str]]) -> None:
        """Add new global variables.

        Parameters:
            value:
                str or list of str
                The new global variable(s) to be added.
        """
        new_vars = set(make_list(value))
        for var in new_vars:
            if not hasattr(self, var):
                raise AttributeError(
                    f"{var} is not a variable in {self.__class__}."
                )
            self._glob_vars.add(var)
        self.notify()

    def attach(self, observer: _Observer) -> None:
        """Add a new observer."""
        self.observers.add(observer)
        observer.notification(self)

    def detach(self, observer: _Observer) -> None:
        """Detach an observer."""
        self.observers.remove(observer)

    def notify(self) -> None:
        """Notify all observers."""
        for observer in self.observers:
            observer.notification(self)


class _Observer(metaclass=ABCMeta):
    """
    Observer is responsible for receiving notifications from the main model.
    """

    def notification(self, notice: _Notice):
        """When the main model changes, the observer will receive a notification."""
        for var in notice.glob_vars:
            value = getattr(notice, var)
            setattr(self, var, value)
