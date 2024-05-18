#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""测试数据收集器。
"""

import pytest

from abses import MainModel, actor


class TestDataCollector:
    """Testing data collector"""

    @pytest.fixture(name="model_cfg")
    def mock_model(self, test_config) -> MainModel:
        """This is a mock model for data collecting tests.
        To use it, you need to include 'model' as an argument of a test case.
        Without `name='model'`, the fixture will be function's name: `mock_model` instead.
        """
        return MainModel(parameters=test_config, seed=42)

    def test_parse_reporters(self, model_cfg: MainModel):
        """Test model variables."""
        # arrange / act
        datacollector = model_cfg.datacollector
        # assert
        assert "var1" in datacollector.model_vars
        assert "var2" in datacollector.model_vars
        assert "var1" in datacollector.agent_reporters
        assert "var2" in datacollector.agent_reporters

    @pytest.mark.parametrize(
        "test, expected_var1",
        [
            ("x", "xx"),
            (1, 2),
            (0.5, 1),
        ],
    )
    def test_model_reporter(self, model_cfg: MainModel, test, expected_var1):
        """Test model reporter."""
        # arrange
        model_cfg.test = test
        datacollector = model_cfg.datacollector
        # act
        model_cfg.run_model()
        model_vars = datacollector.get_model_vars_dataframe()
        # assert
        assert "var1" in model_vars.columns
        assert "var2" in model_vars.columns
        assert model_vars.shape == (model_cfg.time.tick, 2)
        assert model_vars["var1"].mode().item() == expected_var1
        assert model_vars["var2"].mode().item() == test

    def test_agent_records(self, model_cfg: MainModel, farmer_cls: actor):
        """test agent data collector"""
        # arrange
        datacollector = model_cfg.datacollector
        farmer = model_cfg.agents.new(farmer_cls, singleton=True)
        model_cfg.test = 1  # not important
        # act
        model_cfg.run_model()
        agent_vars = datacollector.get_agent_vars_dataframe()

        assert "var1" in agent_vars.columns
        assert "var2" in agent_vars.columns
        result = agent_vars.loc[(1, farmer.unique_id), "var2"]
        assert result == "I am a Farmer"
