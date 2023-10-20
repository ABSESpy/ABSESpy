#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
测试模型的基本组件
"""
import pytest
from omegaconf import DictConfig

from abses.components import _Component


class MainModel:
    """测试模型"""

    def __init__(self, settings: DictConfig) -> None:
        self.settings = settings


def test_component_initialization():
    """
    测试组件的初始化
    """
    model = MainModel(settings={})
    component = _Component(model, "test_component")
    assert isinstance(component.args, DictConfig)
    assert list(component.args.keys()) == component.__args__


def test_component_params():
    """
    Test the initialization of a component with specific parameters.

    This function creates a `MainModel` object with the given settings and then
    creates a `Component` object using the model and the specified component name.
    It asserts that the `params` attribute of the component is equal to the
    expected parameters.
    """
    model = MainModel(
        settings={"test_component": {"param1": "value1", "param2": "value2"}}
    )
    component = _Component(model, "test_component")
    assert component.params == {"param1": "value1", "param2": "value2"}


def test_component_args_property():
    model = MainModel(
        settings={"test_component": {"param1": "value1", "param2": "value2"}}
    )
    component = _Component(model, "test_component")
    component.add_args(["param1"])
    assert component.args == DictConfig({"param1": "value1"})


def test_component_args_setter_string():
    model = MainModel(settings={"test_component": {"param3": "value3"}})
    component = _Component(model, "test_component")
    component.add_args("param3")
    assert "param3" in component.args


def test_component_args_setter_iterable():
    model = MainModel(
        settings={"test_component": {"param4": "value4", "param5": "value5"}}
    )
    component = _Component(model, "test_component")
    component.add_args(["param4", "param5"])
    assert "param4" in component.args
    assert "param5" in component.args


def test_component_args_setter_invalid_arg():
    model = MainModel(settings={})
    component = _Component(model, "test_component")
    with pytest.raises(KeyError, match="Argument param6 not found."):
        component.add_args("param6")
