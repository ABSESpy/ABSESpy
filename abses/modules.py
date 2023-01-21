#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/
from __future__ import annotations

from collections.abc import Iterable
from typing import List, Optional, Set, Union

import numpy as np
from agentpy import Model
from prettytable import PrettyTable

from .bases import Creator
from .components import Component, MainComponent, iter_func
from .container import ActorsList, AgentsContainer
from .objects import BaseObj
from .patch import Patch
from .tools.func import make_list


class Module(Component, BaseObj):
    def __init__(self, model: Model, name: Optional[str] = None):
        Component.__init__(self, name=name)
        BaseObj.__init__(self, model, observer=True, name=name)
        self._agents = AgentsContainer(model)
        self._model: Model = model
        self._open: bool = True

    def __repr__(self) -> str:
        if self.opening:
            flag = "open"
        else:
            flag = "closed"
        return f"<{self.name}: {flag}>"

    @property
    def agents(self) -> AgentsContainer:
        return self._agents

    @property
    def opening(self) -> bool:
        return self._open

    def _after_parsing(self):
        self.switch_open_to(self.params.pop("open", None))
        self.recording = self.params.pop("record", [])
        self.reporting = self.recording  # recording vars also reported
        self.reporting = self.params.pop("report", [])

    @iter_func("modules")
    def report_vars(self):
        for var in self._reporting:
            value = getattr(self, var)
            self.model.report(var, value)

    @iter_func("modules")
    def switch_open_to(self, _open: Optional[bool] = None) -> bool:
        """#TODO 思考和说明模块关闭后有何不同"""
        if _open is None:
            return False
        elif not isinstance(_open, bool):
            raise TypeError("Accept boolean parameters")
        else:
            if self._open is not _open:
                self.logger.info(f"{self} switch 'open' to {_open}.")
                self._open = _open
            else:
                pass
        return self._open


# Composite
class CompositeModule(Module, MainComponent, Creator):
    def __init__(self, model: Model, name: str = None) -> None:
        MainComponent.__init__(self, name=name)
        Creator.__init__(self)
        Module.__init__(self, model, name=name)
        self._modules: List[Module] = []

    @property
    def modules(self) -> List[Module]:
        return self._modules

    def summary_modules(self) -> PrettyTable:
        table = PrettyTable()
        table.field_names = ["Name", "Opening", "Params"]
        for module in self.modules:
            table.add_row([module.name, module.opening, len(module.params)])
        return table

    def create_module(self, module_class: Module, *args, **kwargs) -> Module:
        module = module_class(model=self.model, *args, **kwargs)
        if not issubclass(module.__class__, Module):
            raise TypeError("Must inherited from a module.")
        setattr(self, module.name, module)  # register as module
        self.add_creation(module)  # register as creation
        self.modules.append(module)  # register as module
        self.notify()  # update attributes
        return module
