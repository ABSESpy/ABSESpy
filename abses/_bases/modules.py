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

from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterator,
    List,
    Optional,
    Type,
    TypeVar,
)

from loguru import logger

from abses._bases.bases import _Notice
from abses._bases.objects import _BaseObj
from abses._bases.states import _States
from abses.tools.func import iter_func

if TYPE_CHECKING:
    from ..main import MainModel


class Module(_BaseObj):
    """Basic module for the model."""

    def __init__(
        self,
        model: MainModel[Any, Any],
        name: Optional[str] = None,
    ):
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


ModuleType = TypeVar("ModuleType", bound=Module)


class _ModuleFactory(object):
    """To create a module."""

    methods: List[str] = []
    default_cls: type[Module] = Module

    def __init__(self, father) -> None:
        self.father: CompositeModule = father
        self.modules: Dict[str, Module] = {}

    def __iter__(self) -> Iterator[Module]:
        return iter(self.modules.values())

    def _check_cls(
        self, module_cls: Optional[Type[ModuleType]]
    ) -> Type[Module]:
        """Check if the provided class is a valid module class."""
        if module_cls is None:
            return self.default_cls
        if not issubclass(module_cls, self.default_cls):
            raise TypeError(
                f"'{module_cls}' not a subclass of {self.default_cls}."
            )
        return module_cls

    @property
    def is_empty(self) -> bool:
        """If the factory is empty."""
        return len(self.modules.keys()) == 0

    def _check_name(self, name: str) -> None:
        """Check if the name is valid."""
        if name in self.modules:
            raise ValueError(f"Name '{name}' already exists in the model.")

    def new(
        self,
        how: Optional[str] = None,
        module_class: Optional[Type[ModuleType]] = None,
        **kwargs,
    ) -> ModuleType:
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
        self._check_cls(module_cls=module_class)
        if not how:
            module = module_class(model=self.father.model, **kwargs)
        elif hasattr(self, how):
            module = getattr(self, how)(model=self.father.model, **kwargs)
        else:
            raise ValueError(
                f"{how} is not a valid method for creating module."
                f"Choose from {self.methods} for {self.default_cls}"
            )
        # register as module
        self._check_name(module.name)
        self.modules[module.name] = module
        self.father.attach(module)
        return module


# Composite
class CompositeModule(Module, _States, _Notice):
    """基本的组合模块，可以创建次级模块"""

    def __init__(
        self, model: MainModel[Any, Any], name: Optional[str] = None
    ) -> None:
        Module.__init__(self, model, name=name)
        _States.__init__(self)
        _Notice.__init__(self)
        self._modules = _ModuleFactory(self)

    @property
    def modules(self) -> _ModuleFactory:
        """All attached sub-modules."""
        return self._modules

    @property
    def opening(self) -> bool:
        return self._open

    @opening.setter
    def opening(self, value: bool) -> None:
        for module in self.modules:
            module.opening = value
        self._open = value

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

    def create_module(self, module_cls, *args, **kwargs):
        """Create a module."""
        return self.modules.new(module_class=module_cls, *args, **kwargs)
