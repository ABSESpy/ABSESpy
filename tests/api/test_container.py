#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
测试行动者容器。

1. 测试模型的主体容器。
2. 测试单元格的主体容器。
"""

from typing import Dict, List

import pytest

from abses import Actor, MainModel
from abses.container import _AgentsContainer
from abses.errors import ABSESpyError
from abses.nature import PatchCell
from abses.sequences import ActorsList


class TestMainContainer:
    """
    测试用于整个模型的主体容器。
    """

    @pytest.fixture(name="container")
    def test_three_agents_container(
        self, model: MainModel
    ) -> _AgentsContainer:
        """测试用于整个模型的主体容器，用于Examples。"""

        class Actor1(Actor):
            """for testing"""

            test = 1

        class Actor2(Actor):
            """for testing"""

            test = "testing"

        model = MainModel()
        model.agents.new(Actor, singleton=True)
        model.agents.new(Actor1, num=2)
        model.agents.new(Actor2, num=3)
        return model.agents

    def test_empty_container(self, model: MainModel):
        """测试空容器。"""
        # arrange
        container = model.agents
        assert repr(container) == "<ModelAgents: >"

        # act
        container.register(Actor)

        # assert
        assert str(container) == "ModelAgents"
        assert container.is_empty is True
        assert len(container) == 0
        assert container.model is model
        assert container.is_full is False

    def test_register_main(self, model, module):
        """测试注册，注册的主体类型应该在模型的所有 Container 中都自动被注册。"""
        # arrange
        container = model.agents

        # action
        container.register([Actor])

        # assert
        assert all("Actor" in cell.agents.keys() for cell in module)
        assert repr(container) == "<ModelAgents: (0)Actor>"

    def test_create(self, model: MainModel):
        """测试创建主体"""
        # arrange
        container: _AgentsContainer = model.agents

        # action
        actor = container.new(Actor, singleton=True)

        # assert
        assert actor in container.get("Actor")
        assert container.check_registration(Actor)
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
            container.new(breed_cls, n)
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

    def test_get(self, model, admin_cls, farmer_cls):
        """测试获取主体"""
        # arrange
        container = model.agents
        admin = container.new(admin_cls, singleton=True)
        farmer = container.new(farmer_cls, singleton=True)

        # action / assert
        assert container.get("Admin") == {admin}
        assert container.get("Farmer") == {farmer}
        assert container.get() == {admin, farmer}
        assert isinstance(container.get(), ActorsList)

    def test_get_example(self, container):
        """Testing example in container.get()"""

        g1 = container.get("Actor1")
        assert repr(g1) == "<ActorsList: (2)Actor1>"
        assert len(container.get()) == 6

    def test_select_example(self, container: _AgentsContainer):
        """Testing example in container.select()"""
        g1 = container.select("Actor")
        assert repr(g1) == "<ActorsList: (1)Actor>"
        g2 = container.select("test == 1")
        assert repr(g2) == "<ActorsList: (2)Actor1>"
        g3 = container.select({"test": 1})
        assert repr(g3) == "<ActorsList: (2)Actor1>"
        g4 = container.select({"test": "testing"})
        assert repr(g4) == "<ActorsList: (3)Actor2>"

    def test_max_length(self):
        """测试容器的最大长度"""
        # arrange
        model = MainModel(max_agents=4)
        container = model.agents

        # action
        container.new(Actor, 4)

        # assert
        assert container.is_full is True
        assert container.is_empty is False
        assert len(container) == 4
        assert repr(container) == "<ModelAgents: (4)Actor>"
        with pytest.raises(ABSESpyError):
            container.new(Actor, 1)

    def test_main_container(self, model: MainModel, farmer_cls, admin_cls):
        """测试容器的属性"""
        # arrange
        container = model.agents

        # action
        a_farmer = container.new(farmer_cls, singleton=True)
        admins_5 = container.new(admin_cls, 5)
        assert isinstance(a_farmer, Actor)
        assert len(container) == 6
        assert repr(container) == "<ModelAgents: (1)Farmer; (5)Admin>"
        assert container.get("Admin") == admins_5

        # 增删
        another_farmer = farmer_cls(model)
        assert "Farmer" in container.keys()
        container.add(another_farmer)
        container.remove(admins_5[0])
        admins_5[1:3].trigger("die")
        assert repr(container) == "<ModelAgents: (2)Farmer; (2)Admin>"

    @pytest.mark.parametrize(
        "init_breeds, num, breed, expected",
        [
            (["Admin", "Farmer"], (0, 1), None, 1),
            (["Admin", "Farmer"], (1, 1), None, 2),
            (["Admin", "Farmer"], (1, 0), "Admin", 1),
            (["Admin", "Farmer"], (1, 0), "Farmer", 0),
        ],
    )
    def test_has_agent(self, model, breeds, init_breeds, num, breed, expected):
        """测试是否有主体"""
        # arrange
        container: _AgentsContainer = model.agents
        for b, n in zip(init_breeds, num):
            container.new(breeds.get(b), n)

        # act / assert
        assert container.has(breed) == expected


class TestCellContainer:
    """测试单元格容器"""

    def test_register_cell(self, model, cell_0_0):
        """测试注册，注册的主体类型应该在模型的所有 Container 中都自动被注册。"""
        # arrange
        cell_container = cell_0_0.agents

        # action
        cell_container.register([Actor])

        # assert
        assert cell_container.check_registration(Actor)
        assert model.agents.check_registration(Actor)
        assert "Actor" in cell_container.keys()
        assert "Actor" in model.agents.keys()

    def test_add_one(
        self, model: MainModel, cell_0_0: PatchCell, cell_0_1: PatchCell
    ):
        """测试添加一个主体"""
        # arrange / action
        cell_container = cell_0_1.agents
        actor = cell_container.new(Actor, singleton=True)

        # assert
        # 从这里创建的主体应该在直接在该斑块上
        assert actor.on_earth
        assert actor in cell_container
        assert actor in model.agents
        assert len(cell_container) == 1
        assert cell_container.get("Actor") == {actor}
        # 同一个不能被反复添加
        with pytest.raises(ABSESpyError) as e:
            cell_0_0.agents.add(actor)
            e.match(f"{actor} is on another cell thus cannot be added.")
        # 但是可以先移除位置信息，再添加
        cell_0_1.agents.remove(actor)
        cell_0_0.agents.add(actor)
        assert actor.at is cell_0_0

    def test_remove_all(self, model: MainModel, cell_0_0: PatchCell):
        """Test remove cell from everywhere."""
        # arrange
        cell_container = cell_0_0.agents
        actor = cell_container.new(Actor, singleton=True)
        cell_container.remove(actor)

        # assert
        assert actor not in cell_container
        assert actor.at is None
        assert actor in model.agents
