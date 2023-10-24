#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/


from hydra import compose, initialize
from omegaconf import DictConfig

from abses import __version__
from abses.human import BaseHuman
from abses.main import MainModel
from abses.nature import BaseNature

# 加载项目层面的配置
with initialize(version_base=None, config_path="../config"):
    cfg = compose(config_name="testing")


def test_model_attrs():
    """测试模型的默认属性"""
    model = MainModel(parameters=cfg)
    # params 里 1 被 testing.yaml 第一层的 3 覆盖
    # 这个应该出现在
    assert repr(model) == f"<MainModel-{__version__}(init)>"
    assert isinstance(model.settings, DictConfig)
    assert len(model.settings) == len(cfg)
    assert model.params == cfg.model
    assert isinstance(model.human, BaseHuman)
    assert isinstance(model.nature, BaseNature)
    assert model.version == __version__
    assert model.time.strftime("%Y") == "2000"
    assert model.run_id is None
    model2 = MainModel(parameters=cfg, run_id=1)
    assert model2.run_id == 1


def test_time_go():
    """测试模型运行"""
    model = MainModel(parameters=cfg)
    assert model.time.year == 2000
    model.time_go()
    assert model.time.year == model.human.time.year == 2001
    assert model.human.time is model.nature.time

    model.time_go(6)
    assert model.time.year == 2007
