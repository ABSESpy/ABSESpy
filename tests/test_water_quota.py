#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import logging

from abses import MainModel

from .fixtures import setup_water_quota_model

logging.info("Testing water quota model... %s", setup_water_quota_model)


def test_model_attrs(water_quota_model: MainModel):
    """测试模型创建后属性"""
    model = water_quota_model
    assert model.time.year == 1979
    assert model.time.freq == "M"


def test_nature_attrs(water_quota_model: MainModel):
    """测试模型创建后属性"""
    model = water_quota_model
    assert model.nature.crs == "EPSG:4326"
    assert model.nature.irr_lands.shape == (59, 3)  # 读取数据


def test_geo_sphere(water_quota_model: MainModel):
    """测试模型创建后属性"""
    model = water_quota_model
    assert model.nature.crs == "EPSG:4326"


def test_a_farmer_pumping():
    """测试一个主体应该根据他的决策正确抽水"""


def test_data_reader():
    """测试数据读取，前三年都应该随着时间变化，读取到正确的城市、农民数量"""
