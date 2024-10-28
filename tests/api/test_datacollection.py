#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""测试数据收集器。
"""

from typing import Dict, Type

import pytest

from abses import MainModel
from abses.actor import Actor


class TestDataCollector:
    """Testing data collector"""

    @pytest.fixture(name="model_cfg")
    def mock_model(self, test_config) -> MainModel:
        """This is a mock model for data collecting tests.
        To use it, you need to include 'model' as an argument of a test case.
        Without `name='model'`, the fixture will be function's name: `mock_model` instead.
        """
        return MainModel(parameters=test_config, seed=42)

    @pytest.mark.parametrize(
        "name, breed",
        [
            ("var1", "Actor"),
            ("var2", "Farmer"),
        ],
    )
    def test_parse_reporters(self, model_cfg: MainModel, name, breed):
        """Test model variables."""
        # arrange / act
        datacollector = model_cfg.datacollector
        # assert
        assert name in datacollector.model_vars
        assert name in datacollector.agent_reporters[breed]

    @pytest.mark.parametrize(
        "attr, name, value",
        [
            ("test", "var1", "x"),
            ("var2", "var2", 1),
        ],
    )
    def test_model_reporter(self, model_cfg: MainModel, value, name, attr):
        """Test model reporter."""
        # arrange
        setattr(model_cfg, attr, value)
        datacollector = model_cfg.datacollector
        # act
        model_cfg.run_model()
        model_vars = datacollector.get_model_vars_dataframe()
        # assert
        assert name in model_vars.columns
        assert model_vars.shape == (model_cfg.time.tick, 2)
        assert model_vars[name].mode().item() == value

    @pytest.mark.parametrize(
        "breed, attr, name, ticks",
        [
            ("Actor", "test", "var1", 2),
            ("Farmer", "test", "var2", 3),
        ],
    )
    def test_agent_records(
        self,
        model_cfg: MainModel,
        testing_breeds: Dict[str, Type[Actor]],
        breed,
        attr,
        name,
        ticks,
    ):
        """test agent data collector"""
        # arrange
        actor = model_cfg.agents.new(testing_breeds[breed], singleton=True)
        setattr(actor, attr, 1)
        # act
        model_cfg.run_model(steps=ticks)
        agent_vars = model_cfg.datacollector.get_agent_vars_dataframe(breed)

        # assert
        assert name in agent_vars.columns
        result = agent_vars[name]
        assert len(result) == ticks
        assert result.mode().item() == 1
