#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
PyTest fixtures.
"""

import numpy as np
import pytest
from hydra import compose, initialize

from abses import Actor, MainModel
from abses.nature import PatchCell, PatchModule


@pytest.fixture(name="test_config")
def test_config():
    """Test config"""
    with initialize(version_base=None, config_path="config"):
        cfg = compose(config_name="test_config.yaml")
    return cfg


@pytest.fixture(name="water_quota_config")
def test_water_quota_config():
    """Test config"""
    with initialize(version_base=None, config_path="config"):
        cfg = compose(config_name="water_quota.yaml")
    return cfg


@pytest.fixture(name="main_config")
def test_main_config():
    """Test main config"""
    # 加载项目层面的配置
    with initialize(version_base=None, config_path="config"):
        cfg = compose(config_name="testing")
    return cfg


class Farmer(Actor):
    """测试用，另一个类别的主体"""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.metric = 0.1


class Admin(Actor):
    """测试用，另一个类别的主体"""


class City(Actor):
    """测试用，每个城市的主体"""


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
def mock_module(model: MainModel) -> PatchModule:
    """创建一个（2*2）的斑块模块"""
    module: PatchModule = model.nature.create_module(
        how="from_resolution", shape=(2, 2)
    )
    module.apply_raster(
        np.arange(4).reshape(module.shape3d), attr_name="init_value"
    )
    return module


@pytest.fixture(name="cell_0_0", scope="function")
def mock_cell_0_0(module) -> PatchCell:
    """获取模块的第 (0, 0) 个斑块"""
    return module.array_cells[0, 0]


@pytest.fixture(name="cell_0_1", scope="function")
def mock_cell_0_1(module) -> PatchCell:
    """获取模块的第 (0, 1) 个斑块"""
    return module.array_cells[0, 1]


@pytest.fixture(name="cell_1_0", scope="function")
def mock_cell_1_0(module) -> PatchCell:
    """获取模块的第 (1, 0) 个斑块"""
    return module.array_cells[1, 0]


@pytest.fixture(name="cell_1_1", scope="function")
def mock_cell_1_1(module) -> PatchCell:
    """获取模块的第 (1, 1) 个斑块"""
    return module.array_cells[1, 1]


@pytest.fixture(name="cells", scope="function")
def mock_cells(module: PatchModule) -> list:
    """获取模块的所有斑块"""
    return module.array_cells
