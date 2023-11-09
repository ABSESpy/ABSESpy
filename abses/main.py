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
    Base class of a main ABSESpy model.

    Attributes:
        name:
            name of the model. By default, it's the lowercase of class name. E.g.: TestModel -> testmodel.
        settings:
            Structured parameters of the model. Other module or submodules can search the configurations here structurally.
            For an example, if the settings is a nested DictConfig like {'nature': {'test': 3}}, users can access the parameter 'test = 3' by `model.nature.params.test`.
        human:
            The Human module.
        nature:
            The nature module.
        time:
            Time driver.
        params:
            Parameters of the model.
        run_id:
            The run id of the current model. It's useful in batch run.
        agents:
            The container of all agents. One model only has one specific container where all alive agents are stored.
        actors:
            All agents as a list. A model can create multiple lists referring different actors.
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
        """The run id of the current model. It's useful in batch run."""
        return self._run_id

    @property
    def name(self) -> str:
        """name of the model. By default, it's the lowercase of class name. E.g.: TestModel -> testmodel."""
        return self.__class__.__name__

    @property
    def version(self) -> str:
        """Report the current version of this model."""
        return self._version

    @property
    def settings(self) -> DictConfig:
        """Structured parameters of the model. Other module or submodules can search the configurations here structurally.

        For an example, if the settings is a nested DictConfig like {'nature': {'test': 3}}, users can access the parameter 'test = 3' by `model.nature.params.test`.
        """
        return self._settings

    @property
    def agents(self) -> AgentsContainer:
        """The container of all agents. One model only has one specific container where all alive agents are stored."""
        return self._agents

    @property
    def actors(self) -> ActorsList:
        """All agents as a list. A model can create multiple lists referring different actors."""
        return self.agents.to_list()

    @property
    def human(self) -> H:
        """The Human class"""
        return self._human

    @property
    def nature(self) -> N:
        """The Nature module"""
        return self._nature

    @property
    def time(self) -> TimeDriver:
        """The time driver & controller"""
        return self._time

    @property
    def params(self) -> DictConfig:
        """The global parameters of this model."""
        return self.settings.get("model", DictConfig({}))

    def run_model(self) -> None:
        """Start running the model, until the end situation is triggered."""
        self._setup()
        while self.running:
            self.step()
            self.time.go()
            self.time.stdout()
        self._end()

    def setup(self):
        """Users can custom what to do when the model is setup and going to start running."""

    def step(self):
        """A step of the model."""

    def end(self):
        """Users can custom what to do when the model is end."""

    def _setup(self):
        self._trigger("setup", order=("model", "nature", "human"))
        self._trigger("set_state", code=2)

    def _end(self):
        self._trigger("end", order=("nature", "human", "model"))
        self._trigger("set_state", code=3)
