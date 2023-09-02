#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

import logging
from typing import Optional, Tuple

from agentpy import Model
from omegaconf import DictConfig

from abses import __version__

from .bases import Notice
from .container import AgentsContainer
from .human import BaseHuman
from .nature import BaseNature
from .sequences import ActorsList
from .states import States
from .time import TimeDriver
from .tools.func import iter_func

# from .mediator import MainMediator

logger = logging.getLogger(__name__)


class MainModel(Model, Notice, States):
    """
    主模型
    """

    def __init__(
        self,
        name: Optional[str] = "model",
        parameters: DictConfig = DictConfig({}),
        human_class: Optional[BaseHuman] = None,
        nature_class: Optional[BaseNature] = None,
        run_id: Optional[Tuple[int, int]] = None,
    ) -> None:
        Model.__init__(self, _run_id=run_id)
        Notice.__init__(self)
        States.__init__(self)

        if nature_class is None:
            nature_class = BaseNature
        if human_class is None:
            human_class = BaseHuman
        if name is None:
            name = self.__class__.__name__

        self._name: str = name
        self._settings = DictConfig(parameters)
        self._version: str = __version__
        self._human: BaseHuman = human_class(self)
        self._nature: BaseNature = nature_class(self)
        self._agents = AgentsContainer(model=self)
        # setup mediator
        self._time = TimeDriver(model=self)
        # self.mediator = MainMediator(
        #     model=self, human=self.human, nature=self.nature
        # )

    def __repr__(self):
        version = self._version
        return f"<{self.name}-{version}({self.state})>"

    @property
    def name(self) -> str:
        """模型名字"""
        return self._name

    @property
    def version(self) -> str:
        """模型版本"""
        return self._version

    @property
    def settings(self) -> DictConfig:
        """模型的所有参数"""
        return self._settings

    @property
    def agents(self) -> AgentsContainer:
        """模型的所有主体"""
        return self._agents

    @property
    def actors(self) -> ActorsList:
        """列出当前所有主体"""
        return self.agents.to_list()

    @property
    def human(self) -> BaseHuman:
        """人类模块"""
        return self._human

    @property
    def nature(self) -> BaseNature:
        """自然模块"""
        return self._nature

    # @property
    # def registry(self) -> VariablesRegistry:
    #     """变量模块"""
    #     return self._registry

    @property
    def time(self) -> TimeDriver:
        """时间模块"""
        return self._time

    @property
    def params(self) -> DictConfig:
        """模型的参数"""
        return self.settings.get(self.name, DictConfig({}))

    @iter_func("observers")
    def step(self):
        return super().step()

    def time_go(self, steps: int = 1) -> TimeDriver:
        """时间前进"""
        for _ in range(steps):
            self.time.update()
            self.t += 1
            self.step()
            self.update()
        return self.time

    def sim_step(self):
        """Proceeds the simulation by one step, incrementing `Model.t` by 1
        and then calling :func:`Model.step` and :func:`Model.update`."""
        self.time_go()
        if self.t >= self._steps:
            self.running = False
        elif self.time.period >= self.time.end:
            self.running = False
