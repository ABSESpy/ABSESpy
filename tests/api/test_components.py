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

from abses._bases.components import _Component
from abses.main import MainModel


class ArgComponent(_Component):
    """用于测试的，包含强制参数的组件"""

    __args__ = ["param1", "param2"]


class TestComponent:
    """测试模型的基本组件"""

    def _wrap_settings(self, settings: dict, prefix="test"):
        """将输入的配置变成符合格式的形式"""
        return {prefix: settings}

    @pytest.mark.parametrize(
        "module_name",
        [
            ("test_component"),
            ("test_component_"),
        ],
        ids=[
            "Happy path - valid name",
            "Happy path - end with a underscore",
        ],
    )
    def test_init_happy_path(self, model, module_name):
        """
        测试组件的初始化
        """
        # arrange / action
        component = _Component(model, module_name)
        # assert
        assert isinstance(component.args, DictConfig)
        assert list(component.args.keys()) == component.__args__

    @pytest.mark.parametrize(
        "module_name, expected",
        [
            ("_component", ValueError),
            ("TestCapitalize", ValueError),
            (3, TypeError),
            (("test", 111), TypeError),
        ],
        ids=[
            "Invalid name - not start with a underscore",
            "Invalid name - Capitalize",
            "Invalid type - not string",
            "Invalid type - not string",
        ],
    )
    def test_bad_name_init(self, model, module_name, expected):
        """
        测试组件的初始化
        """
        # arrange / action
        with pytest.raises(expected):
            _Component(model, module_name)

    @pytest.mark.parametrize(
        "settings, expected",
        [
            (1, 1),
            ({"testing": 3}, {"testing": 3}),
        ],
        ids=[
            "Happy path - case 1",
            "Happy path - case 2",
        ],
    )
    def test_component_params(self, settings, expected):
        """
        Test the initialization of a component with specific parameters.
        """
        # arrange
        settings = self._wrap_settings(settings=settings)
        model = MainModel(parameters=settings)

        # act
        component = _Component(model, "test")
        assert "test" in model.settings
        assert component.params == expected
        assert component.p == expected

    @pytest.mark.parametrize(
        "settings, expected",
        [
            ({"param1": "value1"}, "value1"),
            ({"param1": 3}, 3),
            ({"param1": 3, "param2": 2}, 3),
        ],
    )
    def test_add_args(self, settings, expected):
        """测试参数的自动选取"""
        # arrange
        settings = self._wrap_settings(settings=settings)
        model = MainModel(parameters=settings)
        component = _Component(model, "test")
        # act
        component.add_args(list(settings["test"].keys()))
        # assert
        assert component.args.param1 == expected
        assert component.args["param1"] == expected

    @pytest.mark.parametrize(
        "settings, arg",
        [
            ({"param1": "value1"}, "param3"),
            ({"param1": 3}, "param3"),
            ({"param1": 3, "param2": 2}, "param3"),
        ],
    )
    def test_adding_unavailable_arg(self, settings, arg):
        """测试添加不可用的参数"""
        # arrange
        settings = self._wrap_settings(settings=settings)
        model = MainModel(parameters=settings)
        component = _Component(model, "test")
        # act
        with pytest.raises(KeyError, match=f"Argument {arg} not found."):
            component.add_args(arg)

    @pytest.mark.parametrize(
        "settings, expected_1, expected_2",
        [
            ({"param1": 1, "param2": 2}, 1, 2),
            ({"param1": 1, "param2": "test"}, 1, "test"),
            ({"param1": 1, "param2": []}, 1, []),
        ],
    )
    def test_start_with_args(self, settings, expected_1, expected_2):
        """测试初始化时带参数"""
        # arrange
        settings = self._wrap_settings(settings=settings)
        model = MainModel(parameters=settings)
        # act
        component = ArgComponent(model, "test")
        # assert
        assert component.params.param1 == expected_1
        assert component.params.param2 == expected_2

    @pytest.mark.parametrize(
        "settings, arg",
        [
            ({"param1": 1}, "param2"),
            ({"param2": 1}, "param1"),
        ],
    )
    def test_fail_start_with_args(self, settings, arg):
        """测试不能成功初始化，因为需要的参数不在"""
        # arrange
        settings = self._wrap_settings(settings=settings)
        model = MainModel(parameters=settings)
        # act / assert
        with pytest.raises(KeyError, match=f"Argument {arg} not found."):
            ArgComponent(model, "test")
