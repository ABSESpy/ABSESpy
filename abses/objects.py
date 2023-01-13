#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

import logging
from typing import List, Optional

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
        Object.__init__(self, model=model)
        Log.__init__(self, name=name)
        Creator.__init__(self)
        self.glob_vars: List[str] = []
        # self.__t = model.t
        if observer:
            model.attach(self)

    # def __setattr__(self, __name: str, __value: Any) -> None:
    #     if hasattr(self, __name):
    #         attr = self.__getattr__(self, __name)
    #         if issubclass(attr.__class__, Variable):
    #             setattr(getattr(attr, 'data'), __name, __value)
    #             return
    #     super().__setattr__(__name, __value)

    def create_variable(self, *args, **kwargs):
        var = Variable.create(*args, **kwargs)
        self.add_creation(var)


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
