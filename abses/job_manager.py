#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

import pandas as pd

if TYPE_CHECKING:
    from .experiment import Experiment
    from .main import MainModel


class ExperimentManager:
    """管理所有实验结果的单例类"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._experiments = {}
            cls._instance._current_exp = None
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_results"):
            self._experiments: Dict[int, "Experiment"] = {}
            self._datasets: Dict[Tuple[int, int], pd.DataFrame] = {}
            self._seeds: Dict[Tuple[int, int], Optional[int]] = {}
            self._overrides: Dict[Tuple[int, int], Dict[str, Any]] = {}

    @property
    def index(self) -> pd.MultiIndex:
        """获取所有实验结果的索引"""
        return pd.MultiIndex.from_tuples(
            self._datasets.keys(), names=["job_id", "repeat_id"]
        )

    def register(self, exp: "Experiment", job_id: int) -> "ExperimentManager":
        """注册一个新实验"""
        self._experiments[job_id] = exp
        return self

    def get_experiment(
        self, job_id: int, repeat_id: int
    ) -> Optional["MainModel"]:
        """获取指定 job_id 的实验"""
        return self._datasets.get((job_id, repeat_id))

    def clean(self) -> None:
        """清理所有实验"""
        self._datasets.clear()

    def update_result(
        self,
        key: Tuple[int, int],
        overrides: Dict[str, Any],
        datasets: MainModel,
        seed: Optional[int] = None,
    ) -> None:
        """更新实验结果"""
        self._datasets[key] = datasets
        self._seeds[key] = seed
        self._overrides[key] = overrides

    def dict_to_df(self, results: dict) -> pd.DataFrame:
        """将嵌套字典转换为 DataFrame

        Args:
            results: 形如 {(job_id, repeat_id): {'metric': value}} 的字典

        Returns:
        包含 job_id, repeat_id 和指标值的 DataFrame
        """
        return pd.DataFrame(results.values(), index=self.index)

    def get_datasets(
        self,
        seed: bool = True,
    ) -> pd.DataFrame:
        """获取所有实验结果的 DataFrame"""
        to_concat = []
        to_concat.append(self.dict_to_df(self._overrides))
        if seed:
            seed = pd.Series(self._seeds, name="seed", index=self.index)
            to_concat.append(seed)
        to_concat.append(self.dict_to_df(self._datasets))
        return pd.concat(to_concat, axis=1).reset_index()
