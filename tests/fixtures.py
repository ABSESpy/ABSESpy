#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import pandas as pd
import pytest
from hydra import compose, initialize

from abses import BaseHuman, BaseNature, MainModel
from abses.actor import Actor

with initialize(version_base=None, config_path="../config"):
    cfg = compose(config_name="water_quota")


class Nature(BaseNature):
    """用作测试用的环境类，模仿 YellowRiver 项目测试一些关键功能"""

    def __init__(self, model, name="nature", crs=cfg.nature.crs):
        super().__init__(model, name="nature", crs=crs)
        self.irr_data = pd.read_csv(cfg.db.irr_data, index_col=0)

    @property
    def irr_lands(self):
        """测试数据能否读取"""
        index = self.irr_data["Year"] == self.time.year
        data = self.irr_data.loc[index].set_index(cfg.city_id)
        return data[list(cfg.crops_id)]


class Farmer(Actor):
    """测试用，另一个类别的主体"""

    def __init__(self, model, observer: bool = True) -> None:
        super().__init__(model, observer)
        self.metric = 0.1


class Admin(Actor):
    """测试用，另一个类别的主体"""


class City(Actor):
    """测试用，每个城市的主体"""


@pytest.fixture(name="water_quota_model")
def setup_water_quota_model() -> MainModel:
    """创造可供测试的黄河灌溉用水例子"""
    # 加载项目层面的配置
    return MainModel(parameters=cfg, nature_class=Nature)
