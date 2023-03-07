#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from .create_tested_instances import simple_main_model


def test_data_exists():
    model = simple_main_model()
    assert model.human.db == {}
