#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from typing import Dict, List

import pytest

from abses import Actor, MainModel
from abses.container import _AgentsContainer


class TestMainContainer:
    """
    测试用于整个模型的主体容器。
    """

    @pytest.fixture(name="model", scope="function")
    def mock_model(self):
        """创建一个模型"""
        return MainModel()

    @pytest.fixture(name="module", scope="function")
    def mock_module(self, model):
        """创建一个（2*2）的斑块模块"""
        return model.nature.create_module(how="from_resolution", shape=(2, 2))

    def test_register(self, model, module):
        """测试注册，注册的主体类型应该在模型的所有 Container 中都自动被注册。"""
        # arrange
        container = model.agents

        # action
        container.register([Actor])

        # assert
        assert all("Actor" in cell.agents.keys() for cell in module)
        assert repr(container) == "<ModelAgents: (0)Actor>"

    def test_create(self, model):
        """测试创建主体"""
        # arrange
        container: _AgentsContainer = model.agents

        # action
        actor = container.create(Actor, singleton=True)

        # assert
        assert actor in container.Actor
        assert repr(container) == "<ModelAgents: (1)Actor>"

    @pytest.mark.parametrize(
        "init_agent, agent_num, expected_repr",
        [
            (["Admin"], [3], "<ModelAgents: (3)Admin>"),
            (
                ["Admin", "Farmer"],
                [3, 2],
                "<ModelAgents: (3)Admin; (2)Farmer>",
            ),
            ([], [], "<ModelAgents: >"),
            (
                ["Admin", "Farmer"],
                [0, 0],
                "<ModelAgents: (0)Admin; (0)Farmer>",
            ),
        ],
        ids=[
            "One breed",
            "Two breeds",
            "Empty container",
            "Empty container but registered two",
        ],
    )
    def test_report(self, model, breeds, init_agent, agent_num, expected_repr):
        """测试汇报模型的样子"""
        # arrange
        container: _AgentsContainer = model.agents
        # action
        for a, n in zip(init_agent, agent_num):
            breed_cls = breeds.get(a)
            container.create(breed_cls, n)
        # assert
        assert repr(container) == expected_repr

    @pytest.mark.parametrize(
        "init_breeds",
        [
            [],
            ["Admin"],
            ["Admin", "Farmer"],
        ],
        ids=[
            "Happy path",
            "One disturbed breed",
            "Two disturbed breeds",
        ],
    )
    def test_setup(
        self, model, init_breeds: List[str], breeds: Dict[str, Actor]
    ):
        """测试模型的初始化"""
        # arrange
        container = model.agents
        container.register([breeds.get(k) for k in init_breeds])

        # action / assert
        assert model.agents is container
        assert str(container) == "<ModelAgents>"
        assert (
            repr(container)
            == f"<ModelAgents: {'; '.join([f'(0){b}' for b in init_breeds])}>"
        )
        assert container.model is model
        # 一个初始化的模型应该有一个容器
        assert isinstance(model.agents, _AgentsContainer)
        # 这个容器是空的
        assert container.is_empty is True
        assert len(container) == 0
        # 这个容器拥有注册的品种
        assert list(container.keys()) == init_breeds
        # 每个品种都是一个空的集合
        assert tuple(container.values()) == tuple(set() for _ in init_breeds)

    def test_main_container(self, model, farmer_cls, admin_cls):
        """测试容器的属性"""
        # arrange
        container = model.agents

        # action
        a_farmer = container.create(farmer_cls, singleton=True)
        admins_5 = container.create(admin_cls, 5)
        assert isinstance(a_farmer, Actor)
        assert len(container) == 6
        assert repr(container) == "<ModelAgents: (1)Farmer; (5)Admin>"
        assert container.Admin == admins_5

        # 增删
        another_farmer = farmer_cls(model)
        assert "Farmer" in container.keys()
        container.add(another_farmer)
        container.remove(admins_5[0])
        admins_5[1:3].trigger("die")
        assert repr(container) == "<ModelAgents: (2)Farmer; (2)Admin>"
