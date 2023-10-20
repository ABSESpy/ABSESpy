#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import pytest
from omegaconf import DictConfig

from abses.bases import _Notice
from abses.modules import CompositeModule, Module


class MockModel(_Notice):
    """测试用模型"""

    @property
    def settings(self):
        """模型的所有参数"""
        return DictConfig(
            {"TestModule": {"param1": "value1", "param2": 1, "param3": 3.0}}
        )


def test_module_instantiation():
    """测试模块的实例化"""
    model = MockModel()
    module = Module(model, name="TestModule")
    assert module.name == "TestModule"
    assert module.opening is True


def test_module_repr():
    """测试模块的repr"""
    model = MockModel()
    module = Module(model, name="TestModule")
    assert repr(module) == "<TestModule: open>"
    module.switch_open_to(False)
    assert repr(module) == "<TestModule: closed>"


def test_module_opening_property():
    """测试模块的开关属性"""
    model = MockModel()
    module = Module(model)
    assert module.opening is True


def test_module_switch_open_to():
    """测试模块的开关方法"""
    model = MockModel()
    module = Module(model)
    assert module.switch_open_to(False) is False
    assert module.opening is False
    assert module.switch_open_to(True) is True
    assert module.opening is True
    with pytest.raises(TypeError):
        module.switch_open_to("string")
    assert (
        module.switch_open_to(None) is False
    )  # Still False from the previous switch


class TestCompositeModule:
    """测试根模块"""

    @pytest.fixture
    def model(self):
        """一个测试用模型，拥有参数"""
        return MockModel()

    @pytest.fixture
    def composite_module(self, model):
        """创建一个基本的父级模块"""
        return CompositeModule(model=model, name="TestModule")

    class DummyModule(Module):
        """继承自Module的测试类"""

        def initialize(self):
            self.switch_open_to(False)

    class NonModuleClass:
        """不能被添加到模型中的测试类"""

    def test_create_module(self, composite_module: CompositeModule):
        """测试"""
        module = composite_module.create_module(
            self.DummyModule, name="SubModule1"
        )
        assert isinstance(module, self.DummyModule)
        assert module in composite_module.modules
        assert composite_module.params == {
            "param1": "value1",
            "param2": 1,
            "param3": 3.0,
        }

    def test_create_non_module_raises_error(
        self, composite_module: CompositeModule
    ):
        """不是模块的类添加时会报错"""
        with pytest.raises(TypeError):
            composite_module.create_module(self.NonModuleClass)

    def test_initialization(self, composite_module: CompositeModule):
        """测试初始化"""
        # You can add assertions here, but without more detailed logic for initialization,
        # there isn't much to check at the moment.
        module = composite_module.create_module(self.DummyModule)
        assert module.opening
        assert composite_module.initialize() is None
        assert module.opening is False
