#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Tuple, Type

import pandas as pd

if TYPE_CHECKING:
    from .experiment import HookFunc
    from .main import MainModel


class ExperimentManager:
    """管理所有实验结果的单例类"""

    _instance = None
    model_cls: Type[MainModel]

    def __new__(cls, model_cls: Type[MainModel]):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.model_cls = model_cls
        return cls._instance

    def __init__(self, model_cls: Type[MainModel]):
        assert self.model_cls is model_cls, "model_cls must be set in __new__"
        if not hasattr(self, "_datasets"):
            self._datasets: Dict[Tuple[int, int], pd.DataFrame] = {}
            self._seeds: Dict[Tuple[int, int], Optional[int]] = {}
            self._overrides: Dict[Tuple[int, int], Dict[str, Any]] = {}
            self._hooks: Dict[str, HookFunc] = {}

    @property
    def hooks(self) -> Dict[str, HookFunc]:
        """获取所有钩子"""
        return self._hooks

    @property
    def index(self) -> pd.MultiIndex:
        """获取所有实验结果的索引"""
        return pd.MultiIndex.from_tuples(
            self._datasets.keys(), names=["job_id", "repeat_id"]
        )

    def clean(self) -> None:
        """清理所有实验"""
        self._datasets.clear()
        self._seeds.clear()
        self._overrides.clear()

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

    def add_a_hook(
        self,
        hook_func: HookFunc,
        hook_name: Optional[str] = None,
    ) -> None:
        """Add a hook to the experiment."""
        if hook_name is None:
            hook_name = hook_func.__name__
        assert (
            hook_name not in self._hooks
        ), f"Hook {hook_name} already exists."
        assert callable(hook_func), "hook_func must be a callable."
        self._hooks[hook_name] = hook_func
