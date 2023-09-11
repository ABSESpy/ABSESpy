#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from typing import Dict, Optional, Type

import numpy as np
import pandas as pd
from omegaconf import DictConfig

from abses import ActorsList, MainModel
from abses.human import BaseHuman
from abses.nature import BaseNature
from examples.water_quota.nature import Nature


class YellowRiver(MainModel):
    """模拟黄河的水资源分配"""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(self, nature_class=Nature, *args, **kwargs)

    @property
    def institution(self) -> str | None:
        if self.time.year <= 1987:
            return None
        if self.time.year <= 1998:
            return "87-WAS"
        if self.time.year <= 2008:
            return "98-UBR"
        raise ValueError(f"{self.time.year} exceed the study period.")

    @property
    def output_now(self) -> pd.DataFrame:
        cols = self.params.recording_attr
        data = {
            "Year": np.full(len(self.farmers), self.time.year),
            "Month": np.full(len(self.farmers), self.time.month),
        } | {col: self.farmers.array(col) for col in cols}
        return pd.DataFrame(data)
