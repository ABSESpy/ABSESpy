#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/
from __future__ import annotations

import logging
from abc import abstractmethod
from typing import Any, List, Optional

from agentpy import Model

from abses.tools.func import iter_func

from .bases import Notice
from .components import Component
from .objects import BaseObj
from .states import States


class Module(Component, BaseObj):
    """基本的模块"""

    def __init__(self, model: Model, name: Optional[str] = None):
        Component.__init__(self, model=model, name=name)
        BaseObj.__init__(self, model, observer=True, name=name)
        self._open: bool = True

    def __repr__(self) -> str:
        flag = "open" if self.opening else "closed"
        return f"<{self.name}: {flag}>"

    def __getattr__(self, __name: str) -> Any:
        return super().__getattribute__(__name)

    @property
    def opening(self) -> bool:
        """模块处于打开或关闭状态"""
        return self._open

    @iter_func("modules")
    def switch_open_to(self, _open: Optional[bool] = None) -> bool:
        """开启或关闭模块，同时开启或关闭所有子模块"""
        if _open is None:
            return False
        if not isinstance(_open, bool):
            raise TypeError("Accept boolean parameters")
        if self._open is not _open:
            logging.info("%s switch 'open' to %s.", self.name, _open)
            self._open = _open
        return self._open

    # @abstractmethod
    def initialize(self):
        """
        Initialization after handle parameters.
        """

    def step(self):
        """
        每当时间前进时触发
        """


# Composite
class CompositeModule(Module, States, Notice):
    """基本的组合模块，可以创建次级模块"""

    def __init__(self, model: Model, name: str = None) -> None:
        States.__init__(self)
        Notice.__init__(self)
        Module.__init__(self, model, name=name)
        self._modules: List[Module] = []

    @property
    def modules(self) -> List[Module]:
        """当前模块的次级模块"""
        return self._modules

    def create_module(self, module_class: Module, *args, **kwargs) -> Module:
        """创建次级模块"""
        module = module_class(model=self._model, *args, **kwargs)
        if not issubclass(module.__class__, Module):
            raise TypeError("Must inherited from a module.")
        setattr(self, module.name, module)  # register as module
        self.attach(module)
        self.modules.append(module)  # register as module
        return module

    @iter_func("modules")
    def initialize(self):
        return super().initialize()
