#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""This file is for multiple-run experiment.
"""
from __future__ import annotations

import copy
import inspect
import itertools
import os
from copy import deepcopy
from numbers import Number
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    cast,
)

import pandas as pd
from loguru import logger

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

import numpy as np
from hydra import compose, initialize
from hydra.core.global_hydra import GlobalHydra
from hydra.core.hydra_config import HydraConfig
from joblib import Parallel, delayed
from omegaconf import DictConfig, OmegaConf
from tqdm.auto import tqdm

from abses.job_manager import ExperimentManager
from abses.main import MainModel

Configurations: TypeAlias = DictConfig | str | Dict[str, Any]
T = TypeVar("T")
HookFunc: TypeAlias = Callable[[MainModel, Optional[int], Optional[int]], Any]


def _parse_path(relative_path: str) -> Path:
    """Parse the path of the configuration file.
    Convert the relpath of current work space to the relpath of this script.
    """
    # 目标绝对路径
    abs_config_file_path = (Path(os.getcwd()) / relative_path).resolve()
    if not abs_config_file_path.is_file():
        raise FileNotFoundError(f"File {abs_config_file_path} not found.")
    # 返回相对于本脚本的路径
    current_file_path = Path(__file__).parent.resolve()
    return relative_path_from_to(current_file_path, abs_config_file_path)


def convert_to_python_type(value: Any) -> Any:
    """Convert numpy types to python native types.
    This function is mainly for `OmegaConfig` module to handle the parameters.
    """
    # If generic one value.
    if isinstance(value, np.generic):
        return value.item()
    # If array
    if isinstance(value, np.ndarray):
        # Optionally convert arrays to list if necessary
        return value.tolist()
    return value


def relative_path_from_to(from_path: Path, to_path: Path) -> Path:
    """Calculate the relative path from one path to another."""
    # 将两个路径都解析为绝对路径
    from_path = from_path.resolve()
    to_path = to_path.resolve()

    # 获取两个路径的公共父目录
    common_ancestor = Path(from_path.anchor)
    # 从根目录向下寻找公共路径
    for part in from_path.parts:
        if (
            to_path.parts[: from_path.parts.index(part) + 1]
            == from_path.parts[: from_path.parts.index(part) + 1]
        ):
            common_ancestor = Path(common_ancestor) / part
        else:
            break

    # 计算从起始路径到公共父目录的距离
    relative_from = Path(
        *[".."] * (len(from_path.relative_to(common_ancestor).parts))
    )
    # 计算从公共父目录到目标路径的距离
    relative_to = to_path.relative_to(common_ancestor)

    # 组合两个部分得到最终的相对路径
    return relative_from / relative_to


def run_single(
    model_cls: Type[MainModel],
    cfg: DictConfig,
    key: Tuple[int, int],
    seed: Optional[int] = None,
    hooks: Optional[Dict[str, HookFunc]] = None,
    **kwargs,
) -> Tuple[Tuple[int, int], Optional[int], pd.DataFrame]:
    """Run model once, return the key, seed, and results.

    Args:
        key:
            The key of the experiment.
        seed:
            The seed of the experiment.
        hooks:
            The hooks to run after the model is run.
    """
    job_id, repeat_id = key
    model = model_cls(
        parameters=cfg,
        run_id=repeat_id,
        seed=seed,
        **kwargs,
    )
    model.run_model()
    results = model.datacollector.get_final_vars_report(model)
    if hooks is not None:
        for hook_name, hook_func in hooks.items():
            logger.info(f"Running hook {hook_name}.")
            _call_hook_with_optional_args(
                hook_func, model, job_id=job_id, repeat_id=repeat_id
            )
    return key, seed, results


class Experiment:
    """Experiment class."""

    def __init__(
        self,
        model_cls: Type[MainModel],
        cfg: Configurations,
        seed: Optional[int] = None,
        **kwargs,
    ):
        if not issubclass(model_cls, MainModel):
            raise TypeError(f"Type {type(model_cls)} is invalid.")
        self._job_id = 0
        self._extra_kwargs = kwargs
        self._overrides: Dict[str, Any] = {}
        self._base_seed = seed
        self._manager = ExperimentManager(model_cls)
        self.cfg = cfg

    @property
    def model_cls(self) -> Type[MainModel]:
        """Model class."""
        return self._manager.model_cls

    @property
    def cfg(self) -> DictConfig:
        """Configuration"""
        return self._cfg

    @cfg.setter
    def cfg(self, cfg: DictConfig):
        # 如果配置是路径，则利用 Hydra API先清洗配置
        if isinstance(cfg, str):
            cfg = _parse_path(cast(str, cfg))
        if isinstance(cfg, Path):
            cfg = self._load_hydra_cfg(cfg)
        assert isinstance(
            cfg, (DictConfig, dict)
        ), f"cfg must be a DictConfig, got {type(cfg)}."
        self._cfg = cfg

    def _is_hydra_parallel(self) -> bool:
        """检查是否在 Hydra 并行环境中"""
        if self.is_hydra_job():
            return self.hydra_config.launcher is not None
        return False

    @classmethod
    def new(
        cls, model_cls: Type[MainModel], cfg: Configurations, **kwargs
    ) -> "Experiment":
        """Create a new experiment for the singleton class `Experiment`.
        This method will delete all currently available exp results and settings.
        Then, it initialize a new instance of experiment.

        Parameters:
            model_cls:
                Using which model class to initialize the experiment.

        Raises:
            TypeError:
                If the model class `model_cls` is not a valid `ABSESpy` model.

        Returns:
            An experiment.
        """
        ExperimentManager(model_cls).clean()
        return cls(model_cls, cfg, **kwargs)

    @property
    def hydra_config(self) -> DictConfig:
        """Hydra config."""
        if self.is_hydra_job():
            return HydraConfig.get()
        raise RuntimeError("Experiment is not running in Hydra.")

    @property
    def folder(self) -> Path:
        """Output dir path."""
        if self.is_hydra_job():
            return Path(self.hydra_config.run.dir)
        return Path(os.getcwd())

    @property
    def outpath(self) -> Path:
        """Output dir path."""
        if self.is_hydra_job():
            return Path(self.hydra_config.runtime.output_dir)
        return self.folder

    @property
    def overrides(self) -> Dict[str, Any]:
        """Overrides"""
        if not self.is_hydra_job():
            return self._overrides
        overrides_dict = {}
        for item in self.hydra_config.overrides.task:
            if "=" in item:  # 确保是键值对形式的覆盖
                key, value = item.split("=", 1)
                overrides_dict[key] = value
        return overrides_dict

    @overrides.setter
    def overrides(self, current_overrides):
        """Set the overrides."""
        if not isinstance(current_overrides, dict):
            raise TypeError("current_overrides must be a dictionary.")
        self._overrides = current_overrides

    @property
    def job_id(self) -> int:
        """Job id.
        Each job means a combination of the configuration.
        If the experiment is running in Hydra, it will return the hydra's job id.
        """
        if self.is_hydra_job():
            return self.hydra_config.job.get("id", 0)
        return self._job_id

    @staticmethod
    def is_hydra_job() -> bool:
        """Returns True if the experiment is running in Hydra."""
        return GlobalHydra().is_initialized()

    def summary(self) -> pd.DataFrame:
        """Summary of the experiment."""
        return self._manager.get_datasets(seed=bool(self._base_seed))

    def _overriding(
        self,
        cfg: DictConfig | Dict[str, Any],
        overrides: Optional[Dict[str, str | Iterable[Number]]] = None,
    ) -> Iterator[DictConfig]:
        """Parse the config."""
        if overrides is None:
            return iter([cfg])
        if isinstance(cfg, dict):
            cfg = DictConfig(cfg)
        keys, values = zip(*overrides.items())
        values = tuple(convert_to_python_type(val) for val in values)
        combinations = itertools.product(*values)
        for comb in combinations:
            cfg_copy = copy.deepcopy(cfg)
            current_overrides = dict(zip(keys, comb))
            for key, val in current_overrides.items():
                OmegaConf.update(cfg_copy, key=key, value=val, merge=True)
            yield cfg_copy, current_overrides

    def _load_hydra_cfg(
        self,
        cfg_path: Path,
        overrides: Optional[Dict[str, str | Iterable[Number]]] = None,
    ) -> Optional[DictConfig]:
        """Initialize Hydra with overrides."""
        if self.is_hydra_job():
            return HydraConfig.get().cfg
        with initialize(version_base=None, config_path=str(cfg_path.parent)):
            cfg = compose(config_name=cfg_path.stem, overrides=overrides)
        return cfg

    # def _get_logging_mode(self, repeat_id: Optional[int] = None) -> str | bool:
    #     log_mode = self.exp_config.get("logging", "once")
    #     if log_mode == "once":
    #         if repeat_id == 1:
    #             logging: bool | str = self.name
    #         else:
    #             return False
    #     elif bool(log_mode):
    #         logging = f"{self.name}_{repeat_id}"
    #     else:
    #         logging = False
    #     return logging

    # def _update_log_config(
    #     self, config, repeat_id: Optional[int] = None
    # ) -> bool:
    #     """Update the log configuration."""
    #     if isinstance(config, dict):
    #         config = DictConfig(config)
    #     OmegaConf.set_struct(config, False)
    #     log_name = self._get_logging_mode(repeat_id=repeat_id)
    #     if not log_name:
    #         config["log"] = False
    #         return config
    #     logging_cfg = OmegaConf.create({"log": {"name": log_name}})
    #     config = OmegaConf.merge(config, logging_cfg)
    #     return config

    def _get_seed(self, repeat_id: int) -> Optional[int]:
        if self._base_seed is None:
            return None
        return self._base_seed + self._job_id * repeat_id + repeat_id

    def _batch_run_repeats(
        self,
        cfg: DictConfig,
        repeats: int,
        number_process: Optional[int] = None,
        display_progress: bool = True,
    ) -> None:
        """运行重复实验"""
        if self._is_hydra_parallel() or number_process == 1:
            # Hydra 并行或指定单进程时，顺序执行
            disable = repeats == 1 or not display_progress
            for repeat_id in tqdm(
                range(1, repeats + 1),
                disable=disable,
                desc=f"Job {self.job_id} repeats {repeats} times.",
            ):
                run_single(
                    model_cls=self.model_cls,
                    cfg=cfg,
                    key=(self.job_id, repeat_id),
                    outpath=self.outpath,
                    seed=self._get_seed(repeat_id),
                    hooks=self._manager.hooks,
                    **self._extra_kwargs,
                )
        else:
            if number_process is None:
                cpu_count = os.cpu_count()
                number_process = max(1, cpu_count or 1 // 2)
                number_process = min(number_process, repeats)

            results = Parallel(
                n_jobs=number_process,
                backend="loky",  # 改用 loky 后端
                verbose=0,
            )(
                delayed(run_single)(
                    model_cls=self.model_cls,
                    cfg=cfg,
                    key=(self.job_id, repeat_id),
                    outpath=self.outpath,
                    seed=self._get_seed(repeat_id),
                    hooks=self._manager.hooks,
                    **self._extra_kwargs,
                )
                for repeat_id in tqdm(
                    range(1, repeats + 1),
                    disable=not display_progress,
                    desc=f"Job {self.job_id} repeats {repeats} times, with {number_process} processes.",
                )
            )
            # 在主进程中批量更新结果
            for key, seed, dataset in results:
                self._manager.update_result(
                    key=key,
                    datasets=dataset,
                    seed=seed,
                    overrides=self.overrides,
                )

    def batch_run(
        self,
        repeats: int = 1,
        parallels: Optional[int] = None,
        display_progress: bool = True,
        overrides: Optional[Dict[str, str | Iterable[Number]]] = None,
    ) -> None:
        """Run the experiment multiple times."""
        cfg = deepcopy(self._cfg)

        if not overrides:
            # 如果没有覆写，直接运行
            self._batch_run_repeats(cfg, repeats, parallels, display_progress)
            return

        # 获取所有配置组合
        all_configs = list(self._overriding(cfg, overrides))
        # 使用一个总进度条
        for config, overrides_ in tqdm(
            all_configs,
            disable=not display_progress,
            desc=f"{len(all_configs)} jobs (repeats {repeats} times each).",
            position=0,
        ):
            self.overrides = overrides_
            # 内层任务只显示简单信息，不显示进度条
            self._batch_run_repeats(
                config,
                repeats,
                parallels,
                display_progress=False,  # 关闭内层进度条
            )
            self._job_id += 1
        self.overrides = {}

    def add_hooks(
        self,
        hooks: List[HookFunc] | Dict[str, HookFunc] | HookFunc,
    ) -> None:
        """Add hooks to the experiment."""
        if hasattr(hooks, "__call__"):
            hooks = [cast(HookFunc, hooks)]
        if isinstance(hooks, (list, tuple)):
            for hook in hooks:
                self._manager.add_a_hook(hook_func=hook)
        elif isinstance(hooks, dict):
            for hook_name, hook_func in hooks.items():
                self._manager.add_a_hook(
                    hook_func=hook_func, hook_name=hook_name
                )
        else:
            raise TypeError(f"Invalid hooks type: {type(hooks)}.")


def _call_hook_with_optional_args(
    hook_func: Callable,
    model: MainModel,
    job_id: Optional[int] = None,
    repeat_id: Optional[int] = None,
) -> Any:
    """根据钩子函数的参数签名动态调用函数

    Args:
        hook_func: 要调用的钩子函数
        model: 模型实例
        job_id: 可选的任务ID
        repeat_id: 可选的重复实验ID
    """
    sig = inspect.signature(hook_func)
    hook_args = {}

    if "job_id" in sig.parameters:
        hook_args["job_id"] = job_id
    if "repeat_id" in sig.parameters:
        hook_args["repeat_id"] = repeat_id

    return hook_func(model, **hook_args)
