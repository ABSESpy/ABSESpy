#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import pytest

from abses import Actor, MainModel
from abses.datacollection import DataCollector
from abses.nature import PatchCell, PatchModule


class Farmer(Actor):
    """测试用，另一个类别的主体"""

    def __init__(self, model, observer: bool = True) -> None:
        super().__init__(model, observer)
        self.metric = 0.1


class Admin(Actor):
    """测试用，另一个类别的主体"""


class City(Actor):
    """测试用，每个城市的主体"""


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

        module = self.nature.create_module(how="from_resolution", shape=(2, 2))

        self.agents.create(MockAgent, self.n - 3)
        self.agents.create(anotherMockAgent, 3)

        positions = module.random_positions(len(self.actors), replace=True)
        for agent, pos in zip(self.actors, positions):
            agent.move.to(pos)

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
                        agentout.move.off()

        self.actors.trigger("write_row")

        self.datacollector.collect()


@pytest.fixture(name="breeds")
def testing_breeds() -> dict:
    """一系列用于测试的主体类型。"""
    return {
        "Farmer": Farmer,
        "Admin": Admin,
        "City": City,
    }


@pytest.fixture
def farmer_cls(breeds):
    """用于测试的农民类型"""
    return breeds.get("Farmer")


@pytest.fixture
def admin_cls(breeds):
    """用于测试的管理者类型"""
    return breeds.get("Admin")


@pytest.fixture(name="model", scope="function")
def mock_model() -> MainModel:
    """创建一个模型"""
    return MainModel()


@pytest.fixture(name="module", scope="function")
def mock_module(model) -> PatchModule:
    """创建一个（2*2）的斑块模块"""
    return model.nature.create_module(how="from_resolution", shape=(2, 2))


@pytest.fixture(name="cell_0_0", scope="function")
def mock_cell_0_0(module) -> PatchCell:
    """获取模块的第 (0, 0) 个斑块"""
    return module.cells[0][0]


@pytest.fixture(name="cell_0_1", scope="function")
def mock_cell_0_1(module) -> PatchCell:
    """获取模块的第 (0, 1) 个斑块"""
    return module.cells[0][1]


@pytest.fixture(name="cell_1_0", scope="function")
def mock_cell_1_0(module) -> PatchCell:
    """获取模块的第 (1, 0) 个斑块"""
    return module.cells[1][0]


@pytest.fixture(name="cell_1_1", scope="function")
def mock_cell_1_1(module) -> PatchCell:
    """获取模块的第 (1, 1) 个斑块"""
    return module.cells[1][1]


@pytest.fixture(name="cells", scope="function")
def mock_cells(module: PatchModule) -> list:
    """获取模块的所有斑块"""
    return module.array_cells
