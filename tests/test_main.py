#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from abses.main import MainModel
from abses.tools.read_files import read_yaml

# r"config/testing.yaml"
"""
model:
    steps: 5
    testing: 1
world: config/world.yaml

groundwater:
    world: config/world.yaml
    string: testing
    nesting:
        world: config/world.yaml
        num: 1
        testing: 2
    float: 0.1

human:
    testing: 1

testing: 3
testing2: [1, 2, 3]
start: 2020-01-01
end: 2022-01-01
"""
CONFIG = r"config/testing.yaml"
config = read_yaml(CONFIG)


def test_model_attrs():
    testing = "test"
    parameters = {"testing": 4, "a": 2}
    model = MainModel(
        name="model",
        base="tests",
        parameters=parameters,
        testing=testing,
        settings_file=CONFIG,
    )
    # params 里 1 被 testing.yaml 第一层的 3 覆盖
    # 这个应该出现在
    assert model.__repr__() == "MainModel-v0.0.1(model): init"
    assert isinstance(model.settings_file, dict)
    assert len(model.settings_file) == len(config)  # settings file is the same
    assert len(model._init_params) == len(parameters)  # (a, settings)
    assert len(model.settings) == len(config) + 1  # 'a' is extra attr

    assert model.settings_file["model"]["testing"] == 1  # basic setting: 1
    assert model.settings_file["testing"] == 3  # basic setting: 3
    assert model._init_params["testing"] == testing  # input
    assert model.settings["testing"] == testing  # using input update file
    # 注意这里只会被一次性使用 key 来替代，在这里 model 优先取走了底层的 testing = 3，human 模块就没法更新了，还是1
    # Notice that first-fold key is used once. Here, model firstly take testing = 3,
    # then Human's testing will not be replaced, keeping human.params['testing'] = 1.
    assert model.params.testing == testing
    assert model.human.params.testing == 1
