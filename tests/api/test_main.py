#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import pytest
from omegaconf import DictConfig

from abses import __version__
from abses.human import BaseHuman
from abses.main import MainModel
from abses.nature import BaseNature


class TestMain:
    """Test MainModel"""

    @pytest.fixture(name="model")
    def fixture_main_model(self, main_config):
        """测试用模型"""
        return MainModel(parameters=main_config)

    def test_model_attrs(self, model: MainModel, main_config: DictConfig):
        """测试模型的默认属性"""
        # params 里 1 被 testing.yaml 第一层的 3 覆盖
        # 这个应该出现在
        assert repr(model) == f"<MainModel-{__version__}(init)>"
        assert isinstance(model.settings, DictConfig)
        assert len(model.settings) == len(main_config)
        assert model.params == main_config.model
        assert isinstance(model.human, BaseHuman)
        assert isinstance(model.nature, BaseNature)
        assert model.version == __version__
        assert model.time.strftime("%Y") == "2000"
        assert model.run_id is None
        model2 = MainModel(parameters=main_config, run_id=1)
        assert model2.run_id == 1

    def test_time_go(self, model: MainModel):
        """测试模型运行"""
        assert model.time.year == 2000
        model.time.go()
        assert model.time.year == model.human.time.year == 2001
        assert model.human.time is model.nature.time

        model.time.go(6)
        assert model.time.year == 2007
