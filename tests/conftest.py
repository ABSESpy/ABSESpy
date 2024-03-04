#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import numpy as np

from abses import Actor, MainModel
from abses.datacollection import DataCollector

# Random Number Generator
rng = np.random.default_rng(42)


class MockAgent(Actor):
    """A mock agent for test."""

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
            agent.move.to(
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
        if self.time.tick == 5:
            self.agents.remove(self.actors[5])

            self.actors[-5:].trigger("make_worse")

            agentout = self.actors[0]
            # Single out the cells attribute
            cells = self.nature.major_layer.cells

            for _row in cells:
                for cell in _row:
                    if agentout in cell.agents:
                        cell.remove(agentout)

        self.actors.trigger("write_row")

        self.datacollector.collect()
