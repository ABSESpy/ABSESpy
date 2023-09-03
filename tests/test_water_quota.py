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
