#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

import logging
from typing import Any, List, Optional

from agentpy import AttrDict
from agentpy.model import Model
from agentpy.objects import Object

from .bases import Creator, Observer
from .log import Log
from .variable import Variable

logger = logging.getLogger(__name__)


class BaseObj(Observer, Log, Object, Creator):
    def __init__(
        self,
        model: Model,
        observer: Optional[bool] = True,
        name: Optional[str] = None,
    ):
        self._vars = AttrDict()
        Object.__init__(self, model=model)
        Log.__init__(self, name=name)
        Creator.__init__(self)
        self.glob_vars: List[str] = []
        # self.__t = model.t
        if observer:
            model.attach(self)

    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name in self.variables:
            self.variables[__name] = __value
        return super().__setattr__(__name, __value)

    @property
    def variables(self):
        return self.__dict__.get("_vars", {})

    def create_var(self, name, long_name, data):
        if name in self.variables:
            raise ValueError("Variable %s already exists" % name)
        var = Variable(name=name, long_name=long_name, initial_value=data)
        self.add_creation(var)
        self.variables[var.name] = var
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
