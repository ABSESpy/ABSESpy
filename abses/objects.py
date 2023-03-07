#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

import logging
from collections import deque
from typing import (
    Any,
    Callable,
    Deque,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Union,
)

import pandas as pd
from agentpy import AttrDict
from agentpy.model import Model
from agentpy.objects import Object
from prettytable import PrettyTable

from abses.time import TimeDriver
from abses.tools.func import make_list

from .bases import Observer
from .log import Log
from .variable import MAXLENGTH, Data, Variable, VariablesRegistry

logger = logging.getLogger(__name__)


class BaseObj(Observer, Log, Object):
    def __init__(
        self,
        model: Model,
        observer: Optional[bool] = True,
        name: Optional[str] = None,
    ):
        Object.__init__(self, model=model)
        Log.__init__(self, name=name)
        self._registry: VariablesRegistry = VariablesRegistry(model=model)
        self._vars_history: Dict[str, Deque[Variable]] = AttrDict()
        self.glob_vars: List[str] = []
        self._recording: Set[str] = set()
        self._reporting: Set[str] = set()
        if observer:
            model.attach(self)

    def __getattr__(self, __name: str) -> Any:
        # if __name in self.vars:
        #     now = super().__getattribute__(__name)
        #     var = self.to_variable(__name, now)
        #     return var.get_value()
        return super().__getattribute__(__name)

    @property
    def vars(self) -> List[str]:
        return self._registry[self]

    @property
    def time(self) -> TimeDriver:
        return self.model.time

    @property
    def db(self) -> Dict:
        return self.model.db

    @property
    def output(self) -> pd.DataFrame:
        return pd.DataFrame(self.log, index=self.time.time[:-1])

    @property
    def recording(self) -> Set[str]:
        return self._recording

    @recording.setter
    def recording(self, variables: Union[str, Iterable[str]]) -> None:
        self._recording = self.recording.union(set(make_list(variables)))

    @property
    def reporting(self) -> Set[str]:
        return self._reporting

    @reporting.setter
    def reporting(self, variables: Union[str, Iterable[str]]) -> None:
        self._reporting = self.reporting.union(make_list(variables))

    def _when_time_go(self):
        self.record(self._recording)
        for var in self._registry[self]:
            value_now = self.__getattr__(var)
            self._vars_history[var].append(value_now)

    def to_variable(self, name, now: Optional[Data] = None) -> Data:
        self._registry.check_variable(name, value=now)
        history = self._vars_history[name]
        return Variable(owner=self, history=history, now=now)

    def register_a_var(
        self,
        name: str,
        init_data: Optional[Data] = None,
        long_name: Optional[str] = None,
        units: Optional[str] = None,
        check_func: Optional[Iterable[Callable]] = None,
    ) -> Variable:
        dtype = type(init_data)
        self._registry.register(
            owner=self,
            var_name=name,
            long_name=long_name,
            units=units,
            dtype=dtype,
            check_func=check_func,
        )
        self._vars_history[name] = deque([], maxlen=MAXLENGTH)
        self.__setattr__(name, init_data)
        return self.to_variable(name=name, now=init_data)

    def report(
        self,
        max_width: int = 30,
        decimal: int = 4,
    ) -> PrettyTable:
        table = PrettyTable()
        table.field_names = ["Variable", "Value"]
        for attr, val in self.__dict__.items():
            if attr in ("id", "type"):
                continue
            if attr.startswith("_"):
                continue
            table.add_row([attr, val])
        table.max_width = max_width
        table.title = f"{self.type} {self.id}:"
        table.float_format = f".{decimal}"
        return table
