#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
The main modelling framework of ABSESpy.
"""

from __future__ import annotations

import sys
from typing import Dict, Generic, List, Optional, Tuple, Type, TypeVar, Union

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

from loguru import logger
from mesa import DataCollector, Model
from mesa.time import BaseScheduler
from omegaconf import DictConfig, OmegaConf

from abses import __version__
from abses.actor import Actor

from .bases import _Notice
from .container import _AgentsContainer
from .human import BaseHuman
from .nature import BaseNature
from .sequences import ActorsList
from .states import _States
from .time import TimeDriver

# Logging configuration
logger.remove(0)
logger.add(
    sys.stderr,
    format="[{time:YYYY-MM-DD HH:mm:ss}][{module:<15}] | {message}",
    level="INFO",
)

# Dynamically load type hints from users' input type
N = TypeVar("N")
H = TypeVar("H")
Reporter: TypeAlias = Dict[str, Union[str, callable]]


class MainModel(Generic[H, N], Model, _Notice, _States):
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
            Parameters of the model, having another alias `.p`.
        run_id:
            The run id of the current model. It's useful in batch run.
        agents:
            The container of all agents.
            One model only has one specific container where all alive agents are stored.
        actors:
            All agents on the earth (added to a specific PatchCell) as a list.
            A model can create multiple lists referring different actors.
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
        _States.__init__(self)

        self._breeds: dict[str, Type[Actor]] = {}
        self._containers: List[_AgentsContainer] = []
        self._settings = DictConfig(parameters)
        self._version: str = __version__
        if not issubclass(human_class, BaseHuman):
            raise TypeError(f"{human_class} is not a subclass of BaseHuman.")
        if not issubclass(nature_class, BaseNature):
            raise TypeError(f"{nature_class} is not a subclass of BaseNature.")
        self._human = human_class(self)
        self._nature = nature_class(self)
        self._agents = _AgentsContainer(
            model=self, max_len=kwargs.get("max_agents")
        )
        self._time = TimeDriver(model=self)
        self._run_id: int | None = run_id
        self.schedule = BaseScheduler(model=self)
        self.initialize_data_collector()
        self._do_each("initialize", order=("nature", "human"))
        self._do_each("set_state", code=1)  # initial state

    def __repr__(self) -> str:
        version = self._version
        return f"<{self.name}-{version}({self.state})>"

    def _do_each(self, _func: str, order: Tuple[str] = None, **kwargs) -> None:
        _obj = {"model": self, "nature": self.nature, "human": self.human}
        if order is None:
            order = ("model", "nature", "human")
        for name in order:
            if name not in _obj:
                raise ValueError(f"{name} is not a valid component.")
            getattr(_obj[name], _func)(**kwargs)

    @property
    def run_id(self) -> int | None:
        """The run id of the current model.
        It's useful in batch run.
        When running a single model, the run id is None.
        """
        return self._run_id

    @property
    def name(self) -> str:
        """name of the model.
        By default, it's the class name.
        """
        return self.__class__.__name__

    @property
    def version(self) -> str:
        """Report the current version of this model."""
        return self._version

    @property
    def settings(self) -> DictConfig:
        """Structured parameters of the model.
        Other module or submodules can search the configurations here structurally.

        For an example, if the settings is a nested DictConfig like {'nature': {'test': 3}},
        users can access the parameter 'test' by both ways:
            1. `model.nature.params.test`.
            2. `model.nature.p.test`.
        """
        return self._settings

    @property
    def agents(self) -> _AgentsContainer:
        """The container of all agents.
        One model only has one specific container where all alive agents are stored.
        Users can access, manipulate, and create agents by this container:

        For instances:
        1. `model.agents.get()` to access all agents.
        2. `model.agents.new(Actor, num=3)` to create 3 agents of Actor.
        3. `model.agents.register(Actor)` to register a new breed of agents to the whole model.
        4. `model.agents.trigger()` to trigger a specific event to all agents.
        """
        return self._agents

    @property
    def actors(self) -> ActorsList:
        """All agents on the earth as an `ActorList`.
        A model can create multiple lists referring different actors.
        """
        return self.agents.get().select({"on_earth": True})

    @property
    def human(self) -> Union[H, BaseHuman]:
        """The Human subsystem."""
        return self._human

    @property
    def nature(self) -> Union[N, BaseNature]:
        """The Nature subsystem."""
        return self._nature

    @property
    def time(self) -> TimeDriver:
        """The time driver & controller"""
        return self._time

    @property
    def params(self) -> DictConfig:
        """The global parameters of this model."""
        return self.settings.get("model", DictConfig({}))

    # alias for model's parameters
    p = params

    @property
    def breeds(self) -> Tuple[str]:
        """All breeds in the model."""
        return tuple(self._breeds.keys())

    @breeds.setter
    def breeds(self, breed: Type[Actor]) -> None:
        """Register a new breed of agents in the model."""
        if not issubclass(breed, Actor):
            raise TypeError(f"{breed} is not a subclass of Actor.")
        self._breeds[breed.breed] = breed
        for container in self._containers:
            container[breed.breed] = set()

    def run_model(self, steps: Optional[int] = None) -> None:
        """Start running the model.

        In order, the model will go through the following steps:
        1. Call `model.setup()` method.
        2. Call `model.step()` method.
        3. Repeating steps, until the end situation is triggered
        4. Call `model.end()` method.
        """
        self._setup()
        while self.running:
            logger.debug(f"Current tick: {self.time.tick}")
            self._step()
            self.time.go()
            if self.time.tick == steps:
                self.running = False
        self._end()

    def setup(self) -> None:
        """Users can custom what to do when the model is setup and going to start running."""

    def step(self) -> None:
        """A step of the model."""

    def end(self) -> None:
        """Users can custom what to do when the model is end."""

    def _setup(self) -> None:
        logger.info(f"Setting up {self.name}...")
        self._do_each("setup", order=("model", "nature", "human"))
        self._do_each("set_state", code=2)

    def _step(self) -> None:
        self._do_each("step", order=("model", "nature", "human"))
        self.schedule.step()
        self.datacollector.collect(self)

    def _end(self) -> None:
        self._do_each("end", order=("nature", "human", "model"))
        self._do_each("set_state", code=3)
        logger.info(f"Ending {self.name}")

    def initialize_data_collector(
        self,
        model_reporters: Optional[Reporter] = None,
        agent_reporters: Optional[Reporter] = None,
        tables: Optional[Reporter] = None,
    ) -> None:
        """Initialize data collector for this ABSESpy Model.
        This method overrides the default `DataCollector` of `mesa.Model`.
        When initializing, users can set the model-level reporters, agent-level reporters,
        and tables not only by parameters but also by config file.

        Parameters:
            model_reporters:
                A dictionary of model-level reporters.
            agent_reporters:
                A dictionary of agent-level reporters.
            tables:
                A list of tables to collect data.

        Example:
        """
        to_reports: DictConfig = self.settings.get(
            "reports", OmegaConf.create({})
        )
        to_reports = OmegaConf.to_container(to_reports, resolve=True)
        reporting_model: DictConfig = to_reports.get("model", {})
        reporting_agents: DictConfig = to_reports.get("agents", {})
        if model_reporters is not None:
            reporting_model.update(model_reporters)
        if agent_reporters is not None:
            reporting_agents.update(agent_reporters)
        _convert_to_python_expression(reporting_model)
        _convert_to_python_expression(reporting_agents)
        self.datacollector = DataCollector(
            model_reporters=reporting_model,
            agent_reporters=reporting_agents,
            tables=tables,
        )


def _convert_to_python_expression(
    expression_dict: dict[str, str]
) -> dict[str, any]:
    """Convert a Python expression string to a Python expression."""
    for key, value in expression_dict.items():
        if value.startswith(":"):
            expression_dict[key] = eval(value[1:])  # pylint: disable=eval-used
