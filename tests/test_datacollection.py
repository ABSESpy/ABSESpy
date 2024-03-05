#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import pytest

from .conftest import MockModel


class Test_DataCollector:
    """Testing data collector"""

    @pytest.fixture(name="model")
    def mock_model(self) -> MockModel:
        """This is a mock model for data collecting tests.
        To use it, you need to include 'model' as an argument of a test case.
        Without `name='model'`, the fixture will be function's name: `mock_model` instead.
        """
        model = MockModel(parameters={"time": {"end": 10}}, seed=42)
        model.run_model()
        return model

    @pytest.mark.parametrize(
        "ratio_1, ratio_2, expected_1, expected_2",
        [
            (2.3333333333333335, 2.0, 10, 4),
            # (2.3333333333333335, 2.0, 10, 4), adding other cases here
        ],
        ids=[
            "Elias' test case",
            # adding other cases' name here
        ],
    )
    def test_model_vars(
        self, model: MockModel, ratio_1, ratio_2, expected_1, expected_2
    ):
        """Test model variables."""
        datacollector = model.datacollector
        assert "const" in datacollector.model_vars
        assert "pop_ratio" in datacollector.model_vars
        ratio = ratio_1  # Implied ratio at beginning
        assert datacollector.model_vars["pop_ratio"][1] == ratio
        ratio = ratio_2  # Implied ratio at end
        assert datacollector.model_vars["pop_ratio"][-1] == ratio
        assert datacollector.model_vars["count_nonnegative"][0] == expected_1
        assert datacollector.model_vars["count_nonnegative"][-1] == expected_2

    def test_agent_records(self, model: MockModel):
        """test agent data collector"""
        datacollector = model.datacollector
        agent_vars = datacollector.get_agent_vars_dataframe()

        assert "const" in agent_vars.columns
        assert "var1" in agent_vars.columns
        assert "on_earth" in agent_vars.columns

        for (step, _), value in agent_vars["var1"].items():
            assert (step + 2) == value

        assert any(
            value is False for (_, _), value in agent_vars["on_earth"].items()
        )

    def test_table_rows(self, model: MockModel):
        """Test table's rows"""
        datacollector = model.datacollector
        table = datacollector.get_table_dataframe("Final Values")
        assert len(table) == 95
        assert "value" in table.columns
        assert "square" in table.columns
