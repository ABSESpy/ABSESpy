#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import pytest

from abses import BaseHuman, MainModel
from abses.nature import BaseNature

CHECK_CODES = []


class MockModel(MainModel):
    """模拟模型，应该自动进行配置"""

    def initialize(self):
        """初始化模型"""
        CHECK_CODES.append("m0")

    def _setup(self):
        """在模型初始化时进行配置"""
        CHECK_CODES.append("m1")

    def step(self):
        """模拟一个步骤"""
        CHECK_CODES.append("m2")

    def _end(self):
        """模拟结束时进行配置"""
        CHECK_CODES.append("m3")


class MockNature(BaseNature):
    """模拟子模块，应该自动进行配置"""

    def initialize(self):
        CHECK_CODES.append("n0")

    def _setup(self):
        """在模型初始化时进行配置"""
        CHECK_CODES.append("n1")

    def step(self):
        """模拟一个步骤"""
        CHECK_CODES.append("n2")

    def _end(self):
        """模拟结束时进行配置"""
        CHECK_CODES.append("n3")


class MockHuman(BaseHuman):
    """模拟人类，应该自动进行配置"""

    def initialize(self):
        CHECK_CODES.append("h0")

    def _setup(self):
        """在模型初始化时进行配置"""
        CHECK_CODES.append("h1")

    def step(self):
        """模拟一个步骤"""
        CHECK_CODES.append("h2")

    def _end(self):
        """模拟结束时进行配置"""
        CHECK_CODES.append("h3")


@pytest.fixture(name="model")
def setup_model():
    """创造可供测试的模型"""
    params = {
        "time": {"freq": "Y", "start": "2000", "end": "2003"},
    }
    return MockModel(
        parameters=params, nature_class=MockNature, human_class=MockHuman
    )


def test_workflow(model: MainModel):
    """测试工作流"""
    assert CHECK_CODES == ["n0", "h0"]
    assert model.state == "init"
    model.setup()
    assert CHECK_CODES == ["n0", "h0", "m1", "n1", "h1"]
    assert model.state == "ready"
    model.step()
    assert CHECK_CODES == ["n0", "h0", "m1", "n1", "h1", "m2"]
    model.step()
    assert CHECK_CODES == ["n0", "h0", "m1", "n1", "h1", "m2", "m2"]
    assert model.state == "ready"
    model.end()
    assert CHECK_CODES == [
        "n0",
        "h0",
        "m1",
        "n1",
        "h1",
        "m2",
        "m2",
        "n3",
        "h3",
        "m3",
    ]
    assert model.state == "complete"
