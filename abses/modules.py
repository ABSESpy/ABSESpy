#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
模型的基本模块。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from loguru import logger

from abses.tools.func import iter_func

from .bases import _Notice
from .objects import _BaseObj
from .states import States

if TYPE_CHECKING:
    from .main import MainModel


class Module(_BaseObj):
    """基本的模块"""

    def __init__(self, model: MainModel, name: Optional[str] = None):
        _BaseObj.__init__(self, model, observer=True, name=name)
        self._open: bool = True

    def __repr__(self) -> str:
        flag = "open" if self.opening else "closed"
        return f"<{self.name}: {flag}>"

    @property
    def opening(self) -> bool:
        """模块处于打开或关闭状态"""
        return self._open

    @opening.setter
    def opening(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError(f"Only accept boolean, got {type(value)}.")
        if self._open is not value:
            logger.info("%s switch 'open' to %s.", self.name, value)
        self._open = value

    def initialize(self):
        """
        Initialization after handle parameters.
        """

    def setup(self):
        """
        Initialization before handle parameters.
        """

    def step(self):
        """
        每当时间前进时触发
        """

    def end(self):
        """
        每当时间后退时触发
        """


# Composite
class CompositeModule(Module, States, _Notice):
    """基本的组合模块，可以创建次级模块"""

    def __init__(self, model: MainModel, name: str = None) -> None:
        Module.__init__(self, model, name=name)
        States.__init__(self)
        _Notice.__init__(self)
        self._modules: List[Module] = []

    @property
    def modules(self) -> List[Module]:
        """当前模块的次级模块"""
        return self._modules

    @Module.opening.setter
    def opening(self, value: bool) -> None:
        for module in self.modules:
            module.opening = value
        Module.opening.fset(self, value)

    def create_module(
        self, module_class: Module, how: Optional[str] = None, **kwargs
    ) -> Module:
        """创建次级模块"""
        if not issubclass(module_class, Module):
            raise TypeError(
                f"Module class {module_class} must inherited from a module."
            )
        if not how:
            module = module_class(model=self._model, **kwargs)
        elif hasattr(module_class, how):
            creating_method = getattr(module_class, how)
            module = creating_method(model=self.model, **kwargs)
        else:
            raise TypeError(f"{how} is not a valid creating method.")
        setattr(self, module.name, module)  # register as module
        self.attach(module)
        self.modules.append(module)  # register as module
        return module

    @iter_func("modules")
    def initialize(self):
        return super().initialize()

    @iter_func("modules")
    def setup(self):
        return super().setup()

    @iter_func("modules")
    def step(self):
        return super().step()

    @iter_func("modules")
    def end(self):
        return super().end()
