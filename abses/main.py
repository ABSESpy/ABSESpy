#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

import logging
from typing import Generic, Optional, Tuple, Type, TypeVar

from mesa import Model
from omegaconf import DictConfig

from abses import __version__

from .bases import _Notice
from .container import AgentsContainer
from .human import BaseHuman
from .nature import BaseNature
from .sequences import ActorsList
from .states import States
from .time import TimeDriver

# from .mediator import MainMediator

logger = logging.getLogger(__name__)

# Dynamically load type hints from users' input type
N = TypeVar("N")
H = TypeVar("H")


class MainModel(Generic[N], Model, _Notice, States):
    """
    主模型
    """

    def __init__(
        self,
        parameters: DictConfig = DictConfig({}),
        human_class: Type[H] = BaseHuman,
        nature_class: Type[N] = BaseNature,
        run_id: Optional[int] = None,
        **kwargs,
    ) -> None:
        Model.__init__(self, **kwargs)
        _Notice.__init__(self)
        States.__init__(self)

        self._settings = DictConfig(parameters)
        self._version: str = __version__
        self._human = human_class(self)
        self._nature = nature_class(self)
        self._agents = AgentsContainer(model=self)
        self._time = TimeDriver(model=self)
        self._run_id: int | None = run_id
        self._trigger("initialize", order=("nature", "human"))
        self._trigger("set_state", code=1)  # initial state

    def __repr__(self):
        version = self._version
        return f"<{self.name}-{version}({self.state})>"

    def _trigger(self, _func: str, order: Tuple[str] = None, **kwargs) -> None:
        _obj = {"model": self, "nature": self.nature, "human": self.human}
        if not order:
            order = ("model", "nature", "human")
        for name in order:
            if name not in _obj:
                raise ValueError(f"{name} is not a valid component.")
            getattr(_obj[name], _func)(**kwargs)

    @property
    def run_id(self) -> int | None:
        """批量运行时，当前模型的运行ID"""
        return self._run_id

    @property
    def name(self) -> str:
        """模型名字"""
        return self.__class__.__name__

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
    def human(self) -> H:
        """人类模块"""
        return self._human

    @property
    def nature(self) -> N:
        """自然模块"""
        return self._nature

    @property
    def time(self) -> TimeDriver:
        """时间模块"""
        return self._time

    @property
    def params(self) -> DictConfig:
        """模型的参数"""
        return self.settings.get("model", DictConfig({}))

    def run_model(self) -> None:
        """模型运行"""
        self.setup()
        while self.running:
            self.step()
            self.time.go()
            self.time.stdout()
        self.end()

    def setup(self):
        """模型的初始化"""
        self._trigger("_setup", order=("model", "nature", "human"))
        self._trigger("set_state", code=2)

    def end(self):
        """模型的结束"""
        self._trigger("_end", order=("nature", "human", "model"))
        self._trigger("set_state", code=3)

    def step(self):
        """模型的一个步骤"""

    def _setup(self):
        """模型的初始化"""

    def _end(self):
        """模型的结束"""
