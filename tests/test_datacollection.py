#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import pytest

from abses import Actor, MainModel
from abses.datacollection import DataCollector
from abses.sequences import ActorsList


class MockAgent(Actor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.val = 0
        self.val2 = 2

    def make_worse(self):
        self.val = -1


class anotherMockAgent(MockAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.val3 = 3


class MockModel(MainModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_var = 100
        self.n = 10

        self.agents.create(MockAgent, self.n - 3)
        self.agents.create(anotherMockAgent, 3)

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
            },
        )

    def step(self):
        if self.time.tick == 5:
            self.agents.remove(self.actors[5])

            self.actors[-5:].trigger("make_worse")

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
        pass

    def test_table_rows(self):
        pass
