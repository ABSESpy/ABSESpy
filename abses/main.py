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

import functools
import json
import os
from datetime import datetime
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

import pandas as pd

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

from mesa import Model
from mesa.time import BaseScheduler
from omegaconf import DictConfig

from abses import __version__
from abses._bases.logging import (
    formatter,
    log_session,
    logger,
    setup_logger_info,
)
from abses.actor import Actor

from ._bases.bases import _Notice
from ._bases.datacollector import ABSESpyDataCollector
from ._bases.states import _States
from .container import _AgentsContainer, _ModelAgentsContainer
from .human import BaseHuman
from .nature import BaseNature
from .sequences import ActorsList
from .time import TimeDriver
from .viz.viz_model import _VizModel

if TYPE_CHECKING:
    from abses import Experiment

# Dynamically load type hints from users' input type
N = TypeVar("N", bound=BaseNature)
H = TypeVar("H", bound=BaseHuman)

SubSystemType: TypeAlias = Literal["model", "nature", "human"]
SubSystem = Union[
    SubSystemType,
    Tuple[SubSystemType, SubSystemType],
    Tuple[SubSystemType, SubSystemType, SubSystemType],
]


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
        human_class: Optional[Type[H]] = None,
        nature_class: Optional[Type[N]] = None,
        run_id: Optional[int] = None,
        outpath: Optional[Path] = None,
        experiment: Optional[Experiment] = None,
        **kwargs: Optional[Any],
    ) -> None:
        Model.__init__(self, **kwargs)
        _Notice.__init__(self)
        _States.__init__(self)
        self._exp = experiment
        self._run_id: Optional[int] = run_id
        self.outpath = cast(Path, outpath)
        self._settings = DictConfig(parameters)
        self._setup_logger(parameters.get("log", {}))
        self.running: bool = True
        self._breeds: Dict[str, Type[Actor]] = {}
        self._containers: List[_AgentsContainer] = []
        self._version: str = __version__
        self._check_subsystems(h_cls=human_class, n_cls=nature_class)
        self._agents = _ModelAgentsContainer(
            model=self, max_len=kwargs.get("max_agents", None)
        )
        self._time = TimeDriver(model=self)
        self.schedule: BaseScheduler = BaseScheduler(model=self)
        self.datacollector: ABSESpyDataCollector = ABSESpyDataCollector(
            parameters.get("reports", {})
        )
        self._do_each("initialize", order=("nature", "human"))
        self._do_each("set_state", code=1)  # initial state

    def __repr__(self) -> str:
        version = self._version
        return f"<{self.name}-{version}({self.state})>"

    def _logging_begin(self) -> None:
        """Logging the beginning of the model."""
        # settings = OmegaConf.to_container(self._settings)
        msg = (
            f"Model: {self.__class__.__name__}\n"
            f"ABSESpy version: {__version__}\n"
            f"Outpath: {self.outpath}\n"
            # f"Model parameters: {json.dumps(settings, indent=4)}\n"
        )
        # logger.bind(data=self._settings).info("Params:")
        log_session(title="MainModel", msg=msg)

    def _logging_step(self) -> None:
        if not self.breeds:
            return
        agents = self.agents.select({"_birth_tick": self.time.tick})
        agents_dict = agents.to_dict()
        lst = [f"{len(lst)} {breed}" for breed, lst in agents_dict.items()]
        msg = (
            f"\nIn [tick {self.time.tick - 1}]:"
            "\n"
            "Created " + ", ".join(lst) + ""
        )
        logger.bind(no_format=True).info(msg)

    def _check_subsystems(
        self, h_cls: Optional[Type[H]], n_cls: Optional[Type[N]]
    ) -> None:
        """Check if the subsystems are correctly set."""
        if h_cls is None:
            h_cls = cast(Type[H], BaseHuman)
        else:
            assert issubclass(h_cls, BaseHuman)
        if n_cls is None:
            n_cls = cast(Type[N], BaseNature)
        else:
            assert issubclass(n_cls, BaseNature)
        self._human = h_cls(self)
        logger.info(f"Human subsystem: {h_cls.__name__}.")
        self._nature = n_cls(self)
        logger.info(f"Natural subsystem: {n_cls.__name__}.")

    def _do_each(
        self,
        _func: str,
        order: SubSystem = ("model", "nature", "human"),
        **kwargs: Any,
    ) -> None:
        _obj = {"model": self, "nature": self.nature, "human": self.human}
        for name in order:
            if name not in _obj:
                raise ValueError(f"{name} is not a valid component.")
            getattr(_obj[name], _func)(**kwargs)

    def _setup_logger(self, log_cfg: Dict[str, Any]) -> None:
        if not log_cfg:
            return
        name = log_cfg.get("name", "logging")
        rotation = log_cfg.get("rotation", "1 day")
        retention = log_cfg.get("retention", "10 days")
        level = log_cfg.get("level", "INFO")
        name = str(name).replace(".log", "")
        logger.add(
            self.outpath / f"{name}.log",
            retention=retention,
            rotation=rotation,
            level=level,
            format=formatter,
        )
        setup_logger_info(self.exp)
        self._logging_begin()  # logging

    @property
    def exp(self) -> Optional[Experiment]:
        """Returns the associated experiment."""
        return self._exp

    @property
    def outpath(self) -> Path:
        """Output path where to deposit assets."""
        return self._outpath

    @outpath.setter
    def outpath(self, path: Optional[Path]) -> None:
        if path is None:
            path = Path(os.getcwd())
        assert path.is_dir(), f"Invalid path {path}"
        self._outpath = path

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
    def agents(self) -> _ModelAgentsContainer:
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
    def actors(self) -> ActorsList[Actor]:
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
    def datasets(self) -> DictConfig:
        """All datasets in the model."""
        return self.settings.get("ds", DictConfig({}))

    # alias for model's datasets
    ds = datasets

    @property
    def breeds(self) -> Dict[str, Type[Actor]]:
        """All breeds in the model."""
        return self._breeds

    @breeds.setter
    def breeds(self, breed: Type[Actor]) -> None:
        """Register a new breed of agents in the model."""
        if not issubclass(breed, Actor):
            raise TypeError(f"{breed} is not a subclass of Actor.")
        self._breeds[breed.breed] = breed
        for container in self._containers:
            container[breed.breed] = set()

    @functools.cached_property
    def plot(self) -> _VizModel:
        """Plotting the model."""
        return _VizModel(self)

    def run_model(self, steps: Optional[int] = None) -> None:
        """Start running the model.

        In order, the model will go through the following steps:
        1. Call `model.setup()` method.
        2. Call `model.step()` method.
        3. Repeating steps, until the end situation is triggered
        4. Call `model.end()` method.
        """
        self._setup()
        while self.running is True:
            self.time.go()
            self._step()
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
        self._do_each("setup", order=("model", "nature", "human"))
        self._do_each("set_state", code=2)
        msg = (
            f"Nature: {str(self.nature.modules)}\n"
            f"Human: {str(self.human.modules)}\n"
        )
        log_session(title="Setting-up", msg=msg)

    def _step(self) -> None:
        self._do_each("step", order=("model", "nature", "human"))
        self.schedule.step()
        self.datacollector.collect(self)
        self._logging_step()

    def _end(self) -> None:
        self._do_each("end", order=("nature", "human", "model"))
        self._do_each("set_state", code=3)
        result = self.datacollector.get_final_vars_report(self)
        msg = (
            "The model is ended.\n"
            f"Total ticks: {self.time.tick}\n"
            f"Final result: {json.dumps(result, indent=4)}\n"
        )
        log_session(title="Ending Run", msg=msg)
        logger.bind(no_format=True).info(f"{datetime.now()}\n\n\n")
        logger.remove()

    def summary(self, verbose: bool = False) -> pd.DataFrame:
        """Report the state of the model."""
        print(f"Using ABSESpy version: {self.version}")
        # Basic reports
        to_report = {
            "name": self.name,
            "state": self.state,
            "tick": self.time.tick,
        }
        for breed in self.agents:
            to_report[breed] = self.agents.has(breed)
        if verbose:
            to_report["model_vars"] = self.datacollector.model_reporters.keys()
            to_report["agent_vars"] = self.datacollector.agent_reporters.keys()
        return pd.Series(to_report)
