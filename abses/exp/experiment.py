#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""This file is for multiple-run experiment.
"""
from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type

import pandas as pd
from hydra.core.hydra_config import HydraConfig
from omegaconf import DictConfig
from tqdm.auto import tqdm

from abses.main import MainModel


class Experiment:
    """Repeated Experiment."""

    _instance = None
    _folder: Path = Path(os.getcwd())
    results: Dict[Tuple[int, int], Any] = {}
    name: Optional[str] = None
    repeats: int = 1
    num_process: int = 1

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Experiment, cls).__new__(cls)
        return cls._instance

    def __init__(
        self,
        model_cls: Optional[Type[MainModel]] = None,
    ):
        self._n_runs = 0
        self._model = model_cls

    @classmethod
    def load_config(cls, cfg: DictConfig) -> None:
        """Loading the configuration of this exp."""
        exp_config: DictConfig = cfg.get("exp", DictConfig({}))
        cls.name = exp_config.get("name")
        cls.repeats = exp_config.get("repeats", 1)
        cls.num_process = exp_config.get("num_process", 1)
        cls._folder = Path(HydraConfig.get().run.dir)

    @property
    def folder(self) -> Path:
        """Output dir path."""
        return self._folder

    @property
    def outpath(self) -> Path:
        """Output dir path."""
        return Path(self.hydra_config.runtime.output_dir)

    @property
    def hydra_config(self) -> DictConfig:
        """Configuration of hydra."""
        return HydraConfig.get()

    @property
    def overrides(self) -> List[str]:
        """Overrides"""
        return self.hydra_config.overrides.task

    @property
    def job_id(self) -> int:
        """Hydra job id."""
        return self.hydra_config.job.get("id", 0)

    def run(
        self, cfg: DictConfig, repeat_id: int, outpath: Optional[Path] = None
    ) -> Dict[str, Any]:
        """运行模型一次"""
        model = self._model(parameters=cfg, run_id=repeat_id, outpath=outpath)
        model.run_model()
        return model.final_report()

    def update(self, reports: Optional[Dict[str, Any]] = None) -> None:
        """Updating in each run."""
        self._n_runs += 1
        self.results[self.job_id, self._n_runs] = reports

    def batch_run(
        self,
        cfg: DictConfig,
        repeats: Optional[int] = None,
        number_process: Optional[int] = None,
        display_progress: bool = True,
    ) -> None:
        """Run the experiment multiple times using multi-processing if specified."""
        self.load_config(cfg=cfg)
        if repeats is None:
            repeats = self.repeats
        if number_process is None:
            number_process = self.num_process
        outpath = self.outpath
        if number_process == 1 or repeats == 1:
            for repeat in tqdm(range(repeats), disable=not display_progress):
                result = self.run(cfg, repeat_id=repeat + 1, outpath=outpath)
                self.update(reports=result)
            return
        # 创建进度条
        with tqdm(total=repeats, disable=not display_progress) as pbar:
            with ProcessPoolExecutor(max_workers=number_process) as executor:
                # 提交所有任务
                futures = [
                    executor.submit(self.run, cfg, repeat_id, outpath)
                    for repeat_id in range(1, repeats + 1)
                ]
                # 使用as_completed等待任务完成
                for future in as_completed(futures):
                    # 每完成一个任务，更新进度条和运行计数
                    reports = future.result()
                    pbar.update()
                    self.update(reports=reports)

    @classmethod
    def summary(cls) -> None:
        """Ending the experiment."""
        return pd.DataFrame(cls.results)
