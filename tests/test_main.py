#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from collections import deque

from abses.components import MainComponent
from abses.main import MainMediator, MainModel
from abses.tools.read_files import read_yaml
from abses.variable import MAXLENGTH

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
    assert model.__repr__() == "<MainModel-v0.1.0(model): init>"
    assert isinstance(model._settings_from_file, dict)
    assert len(model._settings_from_file) == len(
        config
    )  # settings file is the same
    assert len(model._init_params) == len(parameters)  # (a, settings)
    assert len(model.settings) == len(config) + 1  # 'a' is extra attr

    assert (
        model._settings_from_file["model"]["testing"] == 1
    )  # basic setting: 1
    assert model._settings_from_file["testing"] == 3  # basic setting: 3
    assert model._init_params["testing"] == testing  # input
    assert model.settings["testing"] == testing  # using input update file
    # 注意这里只会被一次性使用 key 来替代，在这里 model 优先取走了底层的 testing = 3，human 模块就没法更新了，还是1
    # Notice that first-fold key is used once. Here, model firstly take testing = 3,
    # then Human's testing will not be replaced, keeping human.params['testing'] = 1.
    assert model.params.testing == testing
    assert model.p["testing"] == testing
    assert model.human.params.testing == 1


def test_mediator():
    class TestComponent(MainComponent):
        def __init__(self, name=None):
            MainComponent.__init__(self, name=name)
            self.settings = config
            self._run_id = "testing"
            self.p = {}

        def to_trigger(self, arg="testing"):
            return self.name + " " + arg

        def report_vars(self):
            pass

    model = TestComponent(name="M")
    human = TestComponent(name="H")
    nature = TestComponent(name="N")

    mediator = MainMediator(model=model, nature=nature, human=human)
    assert mediator.__str__() == "<Mediator of: M, H, N>"
    results = mediator.trigger_functions("human", "to_trigger")
    assert results.human == "H testing"
    assert results.nature is None and results.model is None
    results = mediator.trigger_functions("nature", "to_trigger", "test")
    assert results.nature == "N test"

    mediator._change_state(2)
    assert mediator._states_are("ready", how="all")
    human.state = 3
    assert mediator._states_are("complete", how="any")
    assert not mediator._states_are("complete", how="all")
    try:
        mediator._check_sender("wrong sender")
    except TypeError as e:
        assert "Type of sender" in e.__str__()
        assert "str" in e.__str__()
    mediator._check_sender(model)
    assert mediator.sender == "model"


def test_time_go():
    model = MainModel(base="tests", name="test_time_go")
    assert model.time.year == 2000
    model.human.register_a_var(
        "test",
        1,
        "test_time_go",
    )
    model.nature.register_a_var(
        "test",
        1,
        "test_time_go",
    )
    model.time_go()
    assert model.time.year == model.human.time.year == 2001
    assert model.human.time is model.nature.time
    human_test_result = deque([1], maxlen=MAXLENGTH)
    nature_test_result = deque([1], maxlen=MAXLENGTH)
    human_now = 1
    nature_now = 1
    for i in range(6):
        model.human.test += i
        model.nature.test *= i
        human_now += i
        nature_now *= i
        human_test_result.append(human_now)
        nature_test_result.append(nature_now)
        model.time_go()
    assert model.human._vars_history["test"] == human_test_result
    assert model.nature._vars_history["test"] == nature_test_result
