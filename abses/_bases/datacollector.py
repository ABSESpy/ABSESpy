#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""数据收集器
"""
from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    cast,
)

import numpy as np
import pandas as pd
from loguru import logger

if TYPE_CHECKING:
    from abses.actor import Actor
    from abses.main import MainModel
    from abses.sequences import ActorsList
    from abses.time import TimeDriver

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

Reporter: TypeAlias = Callable[..., Any]
ReporterDict: TypeAlias = Dict[str, Reporter]
ReportType: TypeAlias = Literal["model", "agents", "final"] | str


def _getattr_to_reporter(
    attribute_name: str,
) -> Callable[..., Any]:
    """获取属性的报告函数"""

    def attr_reporter(obj: Actor | MainModel):
        return getattr(obj, attribute_name, None)

    return attr_reporter


def _func_reporter(reporter: List) -> Callable[..., Any]:
    """函数报告器"""
    func, params = reporter[0], reporter[1]

    def func_reporter(agent: Actor):
        return func(agent, *params)

    return func_reporter


def clean_to_reporter(
    reporter: Reporter,
    *args,
    **kwargs,
) -> Callable[..., Any]:
    """将字符串转换为函数"""
    if isinstance(reporter, str):
        reporter = _getattr_to_reporter(attribute_name=reporter)
    elif isinstance(reporter, Iterable):
        reporter = _func_reporter(reporter)
    elif callable(reporter):
        reporter = _func_reporter([reporter, args, kwargs])
    return reporter


class ABSESpyDataCollector:
    """ABSESpyDataCollector, adapted from DataCollector of `mesa`."""

    def __init__(self, reports: Dict[ReportType, Dict[str, Reporter]]):
        self.model_reporters: Dict[str, Reporter] = {}
        self.final_reporters: Dict[str, Reporter] = {}
        self.agent_reporters: Dict[str, Dict[str, Reporter]] = {}

        self._agent_records: Dict[str, List[pd.DataFrame]] = {}
        self.model_vars: Dict[str, List[Any]] = {}

        self.add_reporters("model", reports.get("model", {}))
        self.add_reporters("agents", reports.get("agents", {}))
        self.add_reporters("final", reports.get("final", {}))

    def add_reporters(
        self,
        item: ReportType,
        reporters: ReporterDict,
    ) -> None:
        """Add a dictionary of new reporters."""
        # 处理列表？
        # if isinstance(reporters, (tuple, list)):
        #     reporters = {name: name for name in reporters}
        if item == "model":
            for name, reporter in reporters.items():
                self._new_model_reporter(name=name, reporter=reporter)
            return
        if item == "final":
            for name, reporter in reporters.items():
                self.final_reporters[name] = clean_to_reporter(reporter)
            return
        if item == "agents":
            for breed, tmp_reporters in reporters.items():
                self.add_reporters(
                    item=breed, reporters=cast(ReporterDict, tmp_reporters)
                )
            return
        for name, reporter in reporters.items():
            self._new_agent_reporter(breed=item, name=name, reporter=reporter)

    def _new_model_reporter(self, name: str, reporter: Reporter) -> None:
        """Add a new model-level reporter to collect data.

        Parameters:
            name:
                Name of the model level variable to collect.
            reporter:
                Attribute string,
                or function object that returns the variable.
        """
        self.model_reporters[name] = clean_to_reporter(reporter)
        self.model_vars[name] = []

    def _record_a_breed_of_agents(
        self, time: TimeDriver, breed: str, agents: ActorsList[Actor]
    ) -> None:
        """记录某一组的数据"""
        result = {
            "AgentID": agents.array("unique_id"),
            "Step": np.repeat(time.tick, len(agents)),
            "Time": np.repeat(time.dt, len(agents)),
        }
        for name, reporter in self.agent_reporters[breed].items():
            result[name] = agents.apply(reporter)
        self._agent_records[breed].append(result)

    def _record_agents(self, model: MainModel) -> None:
        """记录所有的Agents"""
        for breed in model.agent_types:
            breed = breed.__name__
            if breed not in self.agent_reporters:
                continue
            if breed not in self._agent_records:
                self._agent_records[breed] = []
            agents = model.agents[breed]
            self._record_a_breed_of_agents(model.time, breed, agents)

    def _new_agent_reporter(
        self, breed: str, name: str, reporter: Reporter
    ) -> None:
        """添加新的 Agent Reporter"""
        if breed not in self.agent_reporters:
            self.agent_reporters[breed] = {}
        self.agent_reporters[breed][name] = clean_to_reporter(
            reporter=reporter
        )

    def get_model_vars_dataframe(self):
        """Create a pandas DataFrame from the model variables.

        The DataFrame has one column for each model variable, and the index is
        (implicitly) the model tick.
        """
        # Check if self.model_reporters dictionary is empty, if so raise warning
        if not self.model_reporters:
            logger.warning(
                "No model reporters have been defined"
                "returning empty DataFrame."
            )

        return pd.DataFrame(self.model_vars)

    def get_agent_vars_dataframe(
        self, breed: Optional[str] = None
    ) -> pd.DataFrame:
        """获取某种 Agents 的 DataFrame"""
        if breed is None:
            return {
                breed: self.get_agent_vars_dataframe(breed)
                for breed in self.agent_reporters
            }
        if not self.agent_reporters:
            logger.warning(
                "No agent reporters have been defined in the DataCollector."
            )
        if results := self._agent_records.get(breed):
            return pd.concat([pd.DataFrame(res) for res in results])
        return pd.DataFrame()

    def get_final_vars_report(self, model: MainModel) -> pd.DataFrame:
        """Report at the end of this model."""
        if not self.final_reporters:
            logger.warning(
                "No final reporters have been defined"
                "returning empty DataFrame."
            )
        return {var: func(model) for var, func in self.final_reporters.items()}

    def collect(self, model: MainModel):
        """Collect all the data for the given model object."""

        if self.model_reporters:
            for var, func in self.model_reporters.items():
                self.model_vars[var].append(func(model))

        if self.agent_reporters:
            self._record_agents(model)
