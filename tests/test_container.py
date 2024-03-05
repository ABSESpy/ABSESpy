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
from abses.errors import ABSESpyError
from abses.nature import PatchCell


class TestMainContainer:
    """
    测试用于整个模型的主体容器。
    """

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
        assert str(container) == "ModelAgents"
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

    def test_max_length(self):
        """测试容器的最大长度"""
        # arrange
        model = MainModel(max_agents=4)
        container = model.agents

        # action
        container.create(Actor, 4)

        # assert
        assert container.is_full is True
        assert container.is_empty is False
        assert len(container) == 4
        assert repr(container) == "<ModelAgents: (4)Actor>"
        with pytest.raises(ABSESpyError):
            container.create(Actor, 1)

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


class TestCellContainer:
    """测试单元格容器"""

    def test_add_one(
        self, model: MainModel, cell_0_0: PatchCell, cell_0_1: PatchCell
    ):
        """测试添加一个主体"""
        # arrange / action
        container = cell_0_1.agents
        actor = container.create(Actor, singleton=True)

        # assert
        # 从这里创建的主体应该在直接在该斑块上
        assert actor.on_earth
        assert actor in container
        assert actor in model.agents
        assert len(container) == 1
        assert container.Actor == {actor}
        # 同一个不能被反复添加
        with pytest.raises(ABSESpyError) as e:
            cell_0_0.agents.add(actor)
            e.match(f"{actor} is on another cell thus cannot be added.")
        # 但是可以先移除位置信息，再添加
        cell_0_1.agents.remove(actor)  # 移除方式
        cell_0_0.agents.add(actor)
        assert actor.at is cell_0_0
        actor.move.off()  # 另一种移除方式
        cell_0_1.agents.add(actor)
        assert actor.at is cell_0_1

    def test_remove_all(self, model: MainModel, cell_0_0: PatchCell):
        """Test remove cell from everywhere."""
        # arrange
        container = cell_0_0.agents
        actor = container.create(Actor, singleton=True)
        actor.die()

        # assert
        assert actor not in container
        assert actor.at is None
        assert actor not in model.agents
