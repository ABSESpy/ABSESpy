#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/
from __future__ import annotations

from collections.abc import Iterable
from typing import List, Optional

import numpy as np
from agentpy import Model
from prettytable import PrettyTable

from .bases import Creation, Creator
from .components import Component, MainComponent, iter_func
from .container import AgentsContainer, BaseAgentList
from .factory import AgentFactory, PatchFactory
from .objects import BaseObj
from .patch import Patch
from .tools.func import make_list, unique_list


class Module(Component, BaseObj):
    def __init__(self, model: Model, name: Optional[str] = None):
        Component.__init__(self, name=name)
        BaseObj.__init__(self, model, observer=True, name=name)
        self._model: Model = model
        self._open: bool = True
        self._recording_vars: List[str] = []
        self._reporting_vars: List[str] = []

    def __repr__(self) -> str:
        if self.opening:
            flag = "open"
        else:
            flag = "closed"
        return f"<{self.name}: {flag}>"

    @property
    def agents(self) -> AgentsContainer:
        return self.model.agents

    @agents.setter
    def agents(self, agents: BaseAgentList) -> None:
        agents = make_list(agents)
        self.agents.add(agents)

    @property
    def opening(self) -> bool:
        return self._open

    @property
    def _rec_vars(self) -> List[str]:
        return self._recording_vars

    @_rec_vars.setter
    def _rec_vars(self, var: List[str]) -> None:
        self._recording_vars = unique_list(self._rec_vars, var)
        self._rep_vars = var

    @property
    def _rep_vars(self) -> List[str]:
        return self._reporting_vars

    @_rep_vars.setter
    def _rep_vars(self, var: Iterable[str]) -> None:
        self._reporting_vars = unique_list(self._rep_vars, var)

    def handle_params(self):
        self.switch_open_to(self.params.pop("open", None))
        self._rec_vars = self.params.pop("record", [])
        self._rep_vars = self.params.pop("report", [])

    @iter_func("modules")
    def record_vars(self) -> None:
        self.record(self._rec_vars)
        self.record(self.glob_vars)

    def parse(self, parameter: str) -> any:
        """
        Generate settings dictionary from setting files.

        Args:
            parameter (str): parameter's name.

        Raises:
            AB_EGMpyError: not correctly formatted settings.

        Returns:
            any: parsed settings.
        """
        return self.params.get(parameter)

    def switch_open_to(self, _open: bool) -> bool:
        if _open is None:
            return False
        elif not isinstance(_open, bool):
            self.logger.error(
                f"Accept boolean parameters, input {type(_open)} instead."
            )
            return False
        else:
            self.logger.info(f"{self.name} switch open state to {_open}!")
            self._open = _open
            return True

    @iter_func("modules")
    def report_vars(self):
        for var in self._rep_vars:
            value = getattr(self, var)
            self.model.report(var, value)


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


# leaf
class LeafModule(Module, Creation):
    def __init__(self, *args, **kwargs) -> None:
        Module.__init__(self, *args, **kwargs)


# class Patch
class PatchModule(PatchFactory, LeafModule):
    def __init__(self, model, name: str = None, **kwargs):
        LeafModule.__init__(self, model, name=name)
        PatchFactory.__init__(self, **kwargs)
        self._patches = []

    @property
    def patches(self):
        return self._patches

    @patches.setter
    def patches(self, patch_name: str) -> None:
        self.creator.transfer_var(self, patch_name)
        self._patches.append(patch_name)

    @property
    def num_attrs(self):
        return self._num_attrs

    @property
    def bool_attrs(self):
        return self._bool_attrs

    def init_variables(self):
        # Hydraulic attributions.
        for attr in self.num_attrs:
            value = self.params.get(attr, 0.0)
            self.create_patch(value, attr, add=True)

        # Type mask with bool dtype.
        for attr in self.bool_attrs:
            value = self.params.get(attr, False)
            self.create_patch(False, attr, add=True)

    def create_patch(self, *args, add=False, **kwargs):
        patch = super().create_patch(*args, **kwargs)
        if add:
            self.add_patch(patch)
        return patch

    def add_patch(self, patch: Patch) -> None:
        self.patches = patch.name
        setattr(self, patch.name, patch)

    def get_patch(self, attr):
        return getattr(self, attr)

    def update_patch(
        self,
        patch_name: str,
        value: "str|int|float|bool|np.ndarray",
        mask: np.ndarray = None,
    ):
        if patch_name in self.patches:
            self.logger.warning(
                f"{patch_name} was created by this module, use 'patch.update()' method instead."
            )
        else:
            self.mediator.transfer_update(
                self, patch_name, value=value, mask=mask
            )
        pass


class HumanModule(AgentFactory, LeafModule):
    def to_agents(self, iterable: Iterable) -> BaseAgentList:
        return BaseAgentList(self.model, iterable)

    def mock(self, agents, attrs, how="attr"):
        tutors = self.to_agents(agents.tutor.now)
        for attr in make_list(attrs):
            values = tutors.array(attr, how)
            agents.update(attr, values)


def skip_if_close(func):
    def skip_module_method(self, *args, **kwargs):
        if self.opening:
            func(self, *args, **kwargs)
        else:
            if self.log_flag:
                self.logger.warning(f"{self}.")

    return skip_module_method
