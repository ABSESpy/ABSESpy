#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

import logging
from collections import deque
from typing import Any, Callable, Deque, Dict, Iterable, List, Optional

from agentpy import AttrDict
from agentpy.model import Model
from agentpy.objects import Object

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
        self._registry: VariablesRegistry = VariablesRegistry(model)
        self._registered_vars: List[str] = []
        self._vars_history: Dict[str, Deque[Variable]] = AttrDict()
        self.glob_vars: List[str] = []
        if observer:
            model.attach(self)

    def __getattr__(self, __name: str) -> Any:
        if __name in self.__dict__.get("_registered_vars"):
            now = super().__getattribute__(__name)
            var = self.to_variable(__name, now)
            return var.get_value()
        else:
            return super().__getattribute__(__name)

    def to_variable(self, name, now: Optional[Data] = None) -> Data:
        self._registry.check_registry(name, value=now)
        history = self._vars_history[name]
        return Variable(owner=self, history=history, now=now)

    # def __setattr__(self, __name: str, __value: Any) -> None:
    #     if __name in self.variables:
    #         self._vars[__name].data = __value
    #     else:
    #         super().__setattr__(__name, __value)

    @property
    def variables(self) -> Dict[str, Variable]:
        return self.__dict__.get("_vars", AttrDict())

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
            name=name,
            long_name=long_name,
            units=units,
            dtype=dtype,
            check_func=check_func,
        )
        self._vars_history[name] = deque([], maxlen=MAXLENGTH)
        var = self.to_variable(name=name, now=init_data)
        return var


class BaseAgent(BaseObj):
    def __init__(self, model: Model, observer: bool = False):
        BaseObj.__init__(self, model, observer=observer, name=self.breed)
        self.setup()

    def __repr__(self) -> str:
        return f"<{self.breed} [{self.id}]>"

    def setup(self):
        pass

    @property
    def breed(self) -> str:
        return self.__class__.__name__.lower()
