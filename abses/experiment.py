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
import itertools
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from numbers import Number
from pathlib import Path
from typing import (
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Tuple,
    Type,
    cast,
)

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

import numpy as np
import pandas as pd
from hydra import compose, initialize
from hydra.core.global_hydra import GlobalHydra
from hydra.core.hydra_config import HydraConfig
from omegaconf import DictConfig, OmegaConf
from tqdm.auto import tqdm

from abses.main import MainModel

Configurations: TypeAlias = DictConfig | str | Dict[str, Any]


def convert_to_python_type(value: Any) -> Any:
    """Convert numpy types to python native types.
    This function is mainly for `OmegaConfig` module to handle the parameters.
    """
    # If generic one value.
    if isinstance(value, np.generic):
        return value.item()
    # If array
    elif isinstance(value, np.ndarray):
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


class Experiment:
    """Repeated Experiment."""

    _instance = None
    folder: Path = Path(os.getcwd())
    hydra_config: DictConfig = DictConfig({})
    name: Optional[str] = None
    final_vars: List[Dict[str, Any]] = []
    model_vars: List[pd.DataFrame] = []

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        model_cls: Optional[Type[MainModel]] = None,
    ):
        self._n_runs = 0
        self._model = model_cls
        self._overrides: Dict[str, Any] = {}
        self._job_id: int = 0

    @classmethod
    def _update_config(
        cls,
        cfg: DictConfig,
        repeats: Optional[int] = None,
        number_process: Optional[int] = None,
    ) -> Tuple[int, int]:
        """Loading the configuration of this exp."""
        exp_config: DictConfig = cfg.get("exp", DictConfig({}))
        if repeats is None:
            repeats = exp_config.get("repeats", 1)
        if number_process is None:
            number_process = exp_config.get("num_process", 1)

        cls.name = exp_config.get("name", "ABSESpyExp")
        if cls.is_hydra_job():
            cls.hydra_config: DictConfig = HydraConfig.get()
            cls.folder = Path(HydraConfig.get().run.dir)
        return repeats, number_process

    @property
    def model(self) -> Optional[Type[MainModel]]:
        """Model class."""
        return self._model

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

    def _is_config_path(self, cfg: Configurations) -> bool:
        if isinstance(cfg, str):
            return True
        if isinstance(cfg, (DictConfig, dict)):
            return False
        raise TypeError(f"Unknown config type {type(cfg)}.")

    def _overriding_config(
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

    def run(
        self, cfg: DictConfig, repeat_id: int, outpath: Optional[Path] = None
    ) -> Tuple[Dict[str, Any], pd.DataFrame]:
        """运行模型一次"""
        if not self._model or not issubclass(self._model, MainModel):
            raise TypeError(f"The model class {self._model} is not valid.")
        model = self._model(parameters=cfg, run_id=repeat_id, outpath=outpath)
        model.run_model()
        if model.datacollector.model_reporters:
            df = model.datacollector.get_model_vars_dataframe()
        else:
            df = pd.DataFrame()
        return model.final_report(), df

    def _update_result(
        self,
        repeat_id: int,
        reports: Optional[Dict[str, Any]] = None,
        model_df: Optional[pd.DataFrame] = None,
    ) -> None:
        """Updating in each run."""
        if reports is None:
            reports = {}
        reports.update(
            {
                "job_id": self.job_id,
                "repeat_id": repeat_id,
            }
        )
        reports |= self.overrides
        self.final_vars.append(reports)
        if model_df is None:
            return
        model_df = model_df.reset_index()
        model_df = model_df.rename({"index": "tick"}, axis=1)
        model_df.insert(0, "repeat_id", repeat_id)
        model_df.insert(0, "job_id", self.job_id)
        self.model_vars.append(model_df)

    def _batch_run_multi_processes(
        self,
        cfg: DictConfig,
        repeats,
        number_process: Optional[int] = 1,
        display_progress: bool = True,
    ):
        # Multiple processes
        with tqdm(total=repeats, disable=not display_progress) as pbar:
            with ProcessPoolExecutor(max_workers=number_process) as executor:
                # 提交所有任务
                futures = [
                    executor.submit(self.run, cfg, repeat_id, self.outpath)
                    for repeat_id in range(1, repeats + 1)
                ]
                # 使用as_completed等待任务完成
                for i, future in enumerate(as_completed(futures)):
                    # 每完成一个任务，更新进度条和运行计数
                    result, model_df = future.result()
                    pbar.update()
                    self._update_result(
                        reports=result, model_df=model_df, repeat_id=i + 1
                    )

    def _batch_run_repeats(self, cfg, repeats, display_progress) -> None:
        for repeat in tqdm(range(repeats), disable=not display_progress):
            result, model_df = self.run(
                cfg, repeat_id=repeat + 1, outpath=self.outpath
            )
            self._update_result(
                reports=result, model_df=model_df, repeat_id=repeat + 1
            )

    def _parse_path(self, relative_path: str) -> Path:
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

    def batch_run(
        self,
        cfg: Configurations,
        repeats: Optional[int] = None,
        parallels: Optional[int] = None,
        display_progress: bool = True,
        overrides: Optional[Dict[str, str | Iterable[Number]]] = None,
    ) -> None:
        """Run the experiment multiple times.

        Parameters:
            cfg:
                The configuration of the experiment.
                It can be either a string of the config file path,
                or a dictionary of the config.
                For an example:
                `cfg='config.yaml'` refers to the config file `config.yaml` saved in the current workspace.
                `cfg={'exp': {'name': 'test', 'repeats': 2}}` refers to the config dictionary.
            repeats:
                The number of repeats for the experiment.
                If not specified, it will use the default value 1 (No repeats).
            parallels:
                The number of processes running in parallel.
                If not specified, it will use the default value 1 (No parallel).
            display_progress:
                Whether to display the progress bar, default True.
            overrides:
                The dictionary of overrides for the experiment.
                If specified, the experiment will sweep all the possible values for the parameter.
                For examples:
                override = {model.key: ["cate1", "cate2"]}
                override = {nature.key: np.arange(10, 2)}
                The first override will lead to two different runs:
                - model.key = cate1
                - model.key = cate2
                The second override will lead to a series runs:
                - model.nature.key = 0.0
                - model.nature.key = 2.0
                - model.nature.key = 4.0
                - model.nature.key = 6.0
                - model.nature.key = 8.0

        Example:
            ```Python
            # initialize the experiment.
            exp = Experiment(MainModel)
            # Loading the configuration file `config.yaml`.
            exp.batch_run('config.yaml')
            ```

            ```Python
            # A different way for initializing.
            exp = Experiment.new(MainModel)
            cfg = {'time': {'end': 25}}

            # Nine runs with different ending ticks.
            exp.batch_run(cfg=cfg, overrides={'time.end': range(10, 100, 10)})
            ```
        """
        # 如果配置是路径，则利用 Hydra API先清洗配置
        if self._is_config_path(cfg):
            config_path = self._parse_path(cast(str, cfg))
            cfg = self._load_hydra_cfg(config_path)
        # 加载配置
        repeats, parallels = self._update_config(cfg, repeats, parallels)
        # 如果没有指定覆写，则直接运行程序
        if not overrides:
            if parallels == 1 or repeats == 1:
                self._batch_run_repeats(cfg, repeats, display_progress)
            else:
                self._batch_run_multi_processes(
                    cfg,
                    repeats,
                    parallels,
                    display_progress,
                )
        # 否则，对每一个复写的配置进行重复运行
        for config, current_overrides in self._overriding_config(
            cfg, overrides
        ):
            self.overrides = current_overrides
            self.batch_run(
                cfg=config,
                repeats=repeats,
                parallels=parallels,
                display_progress=display_progress,
            )
            self._job_id += 1
        # finally, clean up the overrides now.
        self.overrides = {}

    @classmethod
    def summary(cls, save: bool = False, **kwargs) -> None:
        """Ending the experiment."""
        df = pd.DataFrame(cls.final_vars)
        if save:
            df.to_csv(cls.folder / "summary.csv", index=False, **kwargs)
        return df

    @classmethod
    def clean(cls, new_exp: bool = False) -> None:
        """Clean the results.

        Parameters:
            new_exp:
                Whether to create a new experiment.
                If True, it will delete all the current settings.
        """
        cls.final_vars = []
        cls.model_vars = []
        if new_exp:
            cls._instance = None
            cls.folder = Path(os.getcwd())
            cls.hydra_config = DictConfig({})
            cls.name = None

    @classmethod
    def new(cls, model_cls: Optional[Type[MainModel]] = None) -> Experiment:
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
        cls.clean(new_exp=True)
        return cls(model_cls=model_cls)

    @classmethod
    def get_model_vars_dataframe(cls) -> pd.DataFrame:
        """Aggregation of model vars dataframe."""
        if cls.model_vars:
            return pd.concat(cls.model_vars, axis=0)
        raise ValueError("No model vars found.")
