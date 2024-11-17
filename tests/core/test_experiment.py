#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-

"""测试实验相关功能的模块。
这个模块主要测试:
1. 实验的基本配置加载
2. 实验的运行功能
3. 实验的并行计算
4. 实验的钩子函数
5. 实验结果的收集
"""

import pytest

from abses import MainModel
from abses.experiment import Experiment
from tests.helper import RandomAddingMod


class TestExperimentBasic:
    """测试实验的基本功能"""

    def test_experiment_initialization(self, test_config):
        """测试实验的初始化"""
        exp = Experiment.new(MainModel, test_config)
        assert isinstance(exp, Experiment)
        assert exp.cfg == test_config

        class InvalidModel:
            """测试无效的模型类"""

        with pytest.raises(TypeError):
            Experiment.new(InvalidModel, test_config)

    def test_experiment_run(self, test_config):
        """测试实验的运行"""
        exp = Experiment.new(MainModel, test_config)
        exp.batch_run(repeats=2)
        summary = exp.summary()
        assert len(summary) == 2

    def test_experiment_parallel(self, test_config):
        """测试实验的并行计算"""
        exp = Experiment.new(MainModel, test_config)
        exp.batch_run(repeats=4, parallels=2)
        summary = exp.summary()
        assert len(summary) == 4

    def test_experiment_hooks(self, test_config):
        """测试实验的钩子函数"""

        def test_hook(model):
            model.test_hook_called = True

        exp = Experiment.new(MainModel, test_config)
        exp.add_hooks(test_hook)
        exp.batch_run()

    def test_parameter_override(self, test_config):
        """测试参数覆盖功能"""
        exp = Experiment.new(MainModel, test_config)
        overrides = {"param1": [1, 2], "param2": ["a", "b"]}
        exp.batch_run(overrides=overrides)
        summary = exp.summary()
        assert len(summary) == 4


class TestExperimentRandom:
    """测试实验的随机性控制"""

    @pytest.fixture(autouse=True)
    def setup_class(self):
        """在每个测试类运行前重置实验管理器"""
        from abses.job_manager import ExperimentManager

        # 保存当前的实例
        self._original_instance = getattr(ExperimentManager, "_instance")
        # 清空实例
        setattr(ExperimentManager, "_instance", None)
        yield
        # 测试结束后恢复原来的实例
        setattr(ExperimentManager, "_instance", self._original_instance)

    def test_seed_control(self, test_config):
        """测试随机种子控制"""
        # arrange
        exp1 = Experiment.new(RandomAddingMod, test_config, seed=42)
        exp1.batch_run(repeats=3)
        results1 = exp1.summary()

        exp2 = Experiment.new(RandomAddingMod, test_config, seed=42)
        exp2.batch_run(repeats=3)
        results2 = exp2.summary()

        exp3 = Experiment.new(RandomAddingMod, test_config, seed=43)
        exp3.batch_run(repeats=3)
        results3 = exp3.summary()

        # 验证相同种子产生相同结果
        assert results1.equals(results2)
        # 验证不同种子产生不同结果
        assert not results1.equals(results3)
