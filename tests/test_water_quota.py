#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import logging
import os
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest

from abses import MainModel
from examples.water_quota.crops import Crop
from examples.water_quota.farmer import Farmer
from examples.water_quota.yr_human import normalize
from examples.water_quota.yr_nature import Nature

from .fixtures import cfg, setup_water_quota_model

logging.info("Testing water quota model... %s", setup_water_quota_model)


def get_crop_obj(crop: str) -> Crop:
    """根据作物名称获取作物对象"""
    crop_id = cfg.crops_id.get(crop, None)
    path = os.path.join(cfg.db.crops, f"{crop_id}_{crop}.yaml")
    return Crop.load_from(path=path)


def test_model_attrs(water_quota_model: MainModel):
    """测试模型创建后属性"""
    model = water_quota_model
    assert model.time.year == 1979


def test_nature_attrs(water_quota_model: MainModel):
    """测试模型创建后属性"""
    model = water_quota_model
    assert model.nature.crs == "EPSG:4326"
    assert model.nature.irr_lands.shape == (59, 3)  # 读取数据


def test_geo_sphere(water_quota_model: MainModel):
    """测试模型创建后属性"""
    model = water_quota_model
    assert model.nature.crs == "EPSG:4326"


# Fixtures
@pytest.fixture(name="city")
def mock_city():
    city = Mock()
    city.wui = pd.Series({"Maize": 1000})
    return city


@pytest.fixture(name="farmer")
def mock_farmer(city, water_quota_model: MainModel):
    """模拟一个农民用做测试"""
    model = water_quota_model
    farmer = Farmer(model=model, city=city)
    farmer.crop = "Maize"
    return farmer


# Tests
def test_initialization(farmer):
    """初始化农民"""
    assert farmer.city is not None
    assert farmer.crop == "Maize"
    maize = get_crop_obj("Maize")
    curve = maize.curve("M", full=True)
    expected_kc = curve.iloc[farmer.model.time.month - 1]
    assert farmer.Kc == expected_kc
    assert farmer.wui == 1000
    expected_demands = expected_kc / curve.sum() * 1000
    assert farmer.demands == expected_demands


def test_decide_over_withdraw(farmer):
    """农民策略和超用水量"""
    farmer.decision = "C"
    assert farmer.decide_over_withdraw() == 0

    farmer.decision = "D"
    farmer.quota_min = 100
    farmer.quota_max = 200
    farmer.boldness = 0.5
    assert farmer.decide_over_withdraw() == 50  # (200-100) * 0.5


@pytest.fixture(name="real_model")
def real_model_for_test():
    """模拟一个黄河灌溉用水模型"""
    return MainModel(parameters=cfg, nature_class=Nature)


def test_data_reader(real_model: MainModel, farmer: Farmer):
    """测试数据读取，前三年都应该随着时间变化，读取到正确的城市、农民数量"""
    model = real_model
    # 河南，C100，year = 1979
    city = model.nature.cities.select({"unique_id": 100})[0]
    farmer.city = city
    assert farmer.wui == 85.9411215987073
    model.time.go()
    assert farmer.wui == 85.51963447758953
    # Wheat,Rice,Maize
    # 1979: 158.53216605586783,518.8451855740727,85.9411215987073
    # 1980: 157.7546655411846,516.3005764334736,85.51963447758953
    # 1981: 158.81913983884613,519.7843953848551,86.09669159684813


def test_init_social_persons(real_model):
    """测试初始化社会得分的情况"""
    model = real_model
    agents = model.agents.create(Farmer, 5)
    agents.update("s", np.arange(5))
    agent = agents.pop(3)
    assert agent.s == 3.0
    agent.add_friend_from(agents)
    agent.boldness = 1
    agent.clear_mind()
    assert agent.decision == "D"
    agent.change_mind("s", "best")
    assert agent.boldness == agents[-1].boldness
    # 他自己不会批评别人
    agent.boldness = 1
    assert not agent.judge_friends()
    # 其它朋友如果是合作的，就会批评他
    for a in agents:
        a.vengefulness = 1
        a.clear_mind()
        a.add_friend_from([agent])
        assert a.vengefulness == 1
        assert a.friends.__len__() == 1
        assert a.friends[0].decision == "D"
        assert a.dislikes == 0
        criticized = a.judge_friends()
        if a.decision == "D":
            assert not criticized
        else:
            assert criticized


@pytest.mark.parametrize(
    "arr, expected",
    [
        (np.array([0, 1, 2, 3, 4]), np.array([0.0, 0.25, 0.5, 0.75, 1.0])),
        (np.array([0, 0, 0, 0, 0]), np.array([0, 0, 0, 0, 0])),
        (np.array([3, 3, 3, 3, 3]), np.array([0, 0, 0, 0, 0])),
    ],
)
def test_score_calc(real_model, arr, expected):
    """Testing calculate social score"""
    model = real_model
    agents = model.agents.create(Farmer, 5)
    agents.update("s", normalize(arr))
    assert (agents.array("s") == expected).all()
