#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
模型的基本模块。
Basic implementation of the model's module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Type

from loguru import logger

from abses.tools.func import iter_func

from .bases import _Notice
from .objects import _BaseObj
from .states import _States

if TYPE_CHECKING:
    from .main import MainModel


class Module(_BaseObj):
    """Basic module for the model."""

    def __init__(self, model: MainModel, name: Optional[str] = None):
        _BaseObj.__init__(self, model, observer=True, name=name)
        self._open: bool = True

    def __repr__(self) -> str:
        flag = "open" if self.opening else "closed"
        return f"<{self.name}: {flag}>"

    @property
    def opening(self) -> bool:
        """If the module is open."""
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
        Initialization before handle parameters.
        """

    def setup(self):
        """
        Initialization after handle parameters.
        """

    def step(self):
        """
        Called every time step.
        """

    def end(self):
        """
        Called at the end of the simulation.
        """


# Composite
class CompositeModule(Module, _States, _Notice):
    """基本的组合模块，可以创建次级模块"""

    def __init__(self, model: MainModel, name: str = None) -> None:
        Module.__init__(self, model, name=name)
        _States.__init__(self)
        _Notice.__init__(self)
        self._modules: List[Module] = []

    @property
    def modules(self) -> List[Module]:
        """All attached sub-modules."""
        return self._modules

    @Module.opening.setter
    def opening(self, value: bool) -> None:
        for module in self.modules:
            module.opening = value
        Module.opening.fset(self, value)

    def create_module(
        self,
        module_class: Type[Module] = Module,
        how: Optional[str] = None,
        **kwargs,
    ) -> Module:
        """Create a module and attach it to the model.

        Parameters:
            module_class:
                The class of the module to be created.
                Must be a subclass of Module.
                If not given, the default module will be created.
            how:
                The method to create the module.
                If not given, the module will be created by its __init__ method.
            **kwargs:
                The parameters to initialize the module.

        Raises:
            TypeError:
                If the module class is not a subclass of Module.
            ValueError:
                If the creating method is not valid.

        Returns:
            The created module.
        """
        if not issubclass(module_class, Module):
            raise TypeError(
                f"Module {module_class} not inherited from a module."
            )
        if not how:
            module = module_class(model=self._model, **kwargs)
        elif hasattr(module_class, how):
            creating_method = getattr(module_class, how)
            module = creating_method(model=self.model, **kwargs)
        else:
            raise ValueError(f"{how} is not a valid creating method.")
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
