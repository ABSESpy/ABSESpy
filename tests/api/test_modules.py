#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from typing import Any, Dict

import pytest

from abses._bases.modules import CompositeModule, Module
from abses.main import MainModel


class TestModule:
    """测试模块"""

    @pytest.fixture(name="module_test")
    def mock_test_module(self, settings) -> Module:
        """测试模块"""
        model = MainModel(parameters=settings)
        return Module(model, name="test")

    @pytest.fixture(name="settings")
    def mock_settings(self) -> Dict[str, Dict[str, Any]]:
        """模拟设置"""
        settings = {"param1": "value1", "param2": 1, "param3": 3.0}
        return {"test": settings}

    def test_init_module(self, module_test):
        """测试模块的实例化"""
        assert module_test.name == "test"
        assert module_test.opening is True

    @pytest.mark.parametrize(
        "opening, expected",
        [
            (True, "open"),
            (False, "closed"),
        ],
    )
    def test_report(self, module_test, expected, opening):
        """测试模块的repr"""
        # arrange / action
        module_test.opening = opening
        # assert
        assert repr(module_test) == f"<test: {expected}>"

    @pytest.mark.parametrize(
        "switch_to, expected",
        [
            (True, True),
            (False, False),
        ],
    )
    def test_switch_opening(self, module_test, switch_to, expected):
        """测试模块的开关方法"""
        # arrange / action
        result = module_test.opening = switch_to
        # assert
        assert result is expected
        assert module_test.opening is expected


class TestCompositeModule:
    """测试根模块"""

    @pytest.fixture
    def com_module(self, model):
        """创建一个基本的父级模块"""
        return CompositeModule(model=model, name="test")

    def test_create_module(self, com_module: CompositeModule):
        """测试"""
        # arrange / act
        module = com_module.create_module(Module, name="test")
        # assert
        assert isinstance(module, Module)
        assert module in com_module.modules

    def test_create_non_module_raises_error(self, com_module: CompositeModule):
        """不是模块的类添加时会报错"""
        # arrange / act / assert
        with pytest.raises(TypeError):
            com_module.modules.new(module_class=object)

    def test_initialization(self, com_module: CompositeModule) -> None:
        """测试初始化"""
        # arrange / act
        module_1 = com_module.create_module(Module, name="test_1")
        module_2 = com_module.create_module(Module, name="test_2")
        # assert
        com_module.opening = False
        assert not com_module.opening
        assert module_1.opening is False
        assert module_2.opening is False
