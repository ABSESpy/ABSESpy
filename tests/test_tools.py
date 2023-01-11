#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from abses.tools.read_files import is_valid_yaml, read_yaml

CONFIG = r"config/testing.yaml"


def test_parse_yaml():
    params = read_yaml(CONFIG, nesting=False)
    params_all = read_yaml(CONFIG, nesting=True)
    assert is_valid_yaml(params["world"])
    assert is_valid_yaml(params["groundwater"]["world"])
    assert is_valid_yaml(params["groundwater"]["nesting"]["world"])
    assert isinstance(params["world"], str)
    assert isinstance(params_all["world"], dict)
    assert isinstance(params_all["groundwater"]["world"], dict)
    assert isinstance(params_all["groundwater"]["nesting"]["world"], dict)
