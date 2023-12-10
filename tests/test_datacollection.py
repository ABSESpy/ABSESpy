#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import numpy as np
import pytest

from abses import Actor, MainModel
from abses.datacollection import DataCollector
from abses.sequences import ActorsList

# Random Number Generator
rng = np.random.default_rng(42)


class MockAgent(Actor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.val = 0
        self.val2 = 2

    def make_worse(self):
        self.val = -1

    def write_row(self):
        row = {"value": self.val, "square": self.val**2}
        self.model.datacollector.add_table_row("Final Values", row)


class anotherMockAgent(MockAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.val3 = 3


class MockModel(MainModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_var = 100
        self.n = 10

        self.nature.create_module(how="from_resolution", shape=(2, 2))

        self.agents.create(MockAgent, self.n - 3)
        self.agents.create(anotherMockAgent, 3)

        for agent in self.actors:
            agent.put_on_layer(
                layer=self.nature.major_layer,
                pos=tuple(rng.integers(2, size=2)),
            )

        self.datacollector = DataCollector(
            model=self,
            model_reporters={
                "const": "model_var",
                "pop_ratio": lambda m: len(m.agents["MockAgent"])
                / len(m.agents["anotherMockAgent"]),
                "count_nonnegative": lambda m: len(m.actors.better("val", -1)),
            },
            agent_reporters={
                "const": "val2",
                "var1": lambda a: a.val2 + a.model.time.tick,
                "on_earth": "on_earth",
            },
            tables={"Final Values": ["value", "square"]},
        )

    def step(self):
        # Single out the cells attribute
        cells = self.nature.major_layer.cells

        if self.time.tick == 5:
            self.agents.remove(self.actors[5])

            self.actors[-5:].trigger("make_worse")

            agentout = self.actors[0]
            for _row in cells:
                for cell in _row:
                    cell.remove(agentout) if agentout in cell.agents else None

        self.actors.trigger("write_row")

        self.datacollector.collect()


class Test_DataCollector:
    def setup_method(self):
        self.model = MockModel(parameters={"time": {"end": 10}})

        self.model.run_model()

    def test_model_vars(self):
        datacollector = self.model.datacollector
        assert "const" in datacollector.model_vars
        assert "pop_ratio" in datacollector.model_vars
        ratio = 2.3333333333333335  # Implied ratio at beginning
        assert datacollector.model_vars["pop_ratio"][1] == ratio
        ratio = 2.0  # Implied ratio at end
        assert datacollector.model_vars["pop_ratio"][-1] == ratio
        assert datacollector.model_vars["count_nonnegative"][0] == 10
        assert datacollector.model_vars["count_nonnegative"][-1] == 4

    def test_agent_records(self):
        datacollector = self.model.datacollector
        agent_vars = datacollector.get_agent_vars_dataframe()

        assert "const" in agent_vars.columns
        assert "var1" in agent_vars.columns
        assert "on_earth" in agent_vars.columns

        for (step, agentid), value in agent_vars["var1"].items():
            assert (step + 2) == value

        assert any(
            value is False for (_, _), value in agent_vars["on_earth"].items()
        )

    def test_table_rows(self):
        datacollector = self.model.datacollector
        table = datacollector.get_table_dataframe("Final Values")
        assert len(table) == 95
        assert "value" in table.columns
        assert "square" in table.columns
