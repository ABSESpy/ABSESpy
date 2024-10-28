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

import geopandas as gpd
import pytest

from abses import Actor, MainModel
from abses._bases.errors import ABSESpyError
from abses.container import _AgentsContainer, _ModelAgentsContainer
from abses.nature import PatchCell
from abses.tools.data import load_data


class TestBasicContainer:
    """
    测试用于整个模型的主体容器。
    """

    def test_attributes(self, ternary_m):
        """测试创建主体"""
        # arrange
        container: _AgentsContainer = ternary_m.agents

        # action / assert
        assert isinstance(container, _AgentsContainer)
        assert isinstance(container, _ModelAgentsContainer)
        assert str(container) == "<Handling [3]Agents for Test>"
        assert container is ternary_m.agents
        assert getattr(ternary_m, "_all_agents") is getattr(
            container, "_agents"
        )

    def test_add_happy_path(self, model):
        """在主体被创建的时候，应该自动添加到容器中"""
        # arrange
        container: _AgentsContainer = model.agents
        # action
        agent = Actor(model=model)
        # assert
        assert agent in container
        assert len(container) == 1

    @pytest.mark.parametrize(
        "agent_num, breed",
        [
            (3, "Admin"),
            (2, "Farmer"),
            (None, "Farmer"),
        ],
        ids=[
            "One breed",
            "Two breeds",
            "Auto-set singleton",
        ],
    )
    def test_new_agents(self, model, testing_breeds, agent_num, breed):
        """测试创建主体
        容器可以创建任意数量的主体。
        """
        # arrange
        container: _AgentsContainer = model.agents
        breed_cls = testing_breeds.get(breed, None)
        # action
        container.new(breed_cls, num=agent_num)
        # assert
        agent_num = agent_num or 1
        assert str(container) == f"<Handling [{agent_num}]Agents for Test>"

    @pytest.mark.parametrize(
        "agent_num, error_type",
        [
            (0.5, ValueError),
            (-1, ValueError),
        ],
    )
    def test_new_agents_bad_path(self, model, agent_num, error_type):
        """测试创建的主体数量不是非负整数时创建主体失败"""
        # arrange
        container: _AgentsContainer = model.agents
        # action / assert
        with pytest.raises(error_type):
            container.new(Actor, num=agent_num)

    @pytest.mark.parametrize(
        "breeds, expected_number",
        [
            ("Actor", 1),
            ("Farmer", 1),
            (("Actor", "Farmer"), 2),
            (["Actor", "Farmer"], 2),
        ],
    )
    def test_getitem(self, ternary_m, breeds, expected_number):
        """测试获取主体"""
        # arrange
        container = ternary_m.agents
        # action / assert
        assert len(container[breeds]) == expected_number


class TestCellContainer:
    """测试单元格容器"""

    @pytest.mark.parametrize(
        "breed, num",
        [
            ("Actor", 1),
            ("Farmer", None),
            ("Admin", 3),
        ],
    )
    def test_new_one(
        self, ternary_m, cell_0_0: PatchCell, testing_breeds, breed, num
    ):
        """测试直接在斑块上新建主体"""
        # arrange
        assert cell_0_0.model is ternary_m
        len_before = len(ternary_m.agents)
        # action
        actors = cell_0_0.agents.new(
            testing_breeds[breed], num, singleton=False
        )
        actor = actors.item()

        # assert
        # 从这里创建的主体应该在直接在该斑块上
        assert actor.on_earth
        assert actor in cell_0_0.agents
        assert actor in cell_0_0.model.agents
        # 模型中的主体数量应该增加一个
        assert len(cell_0_0.agents) == num or 1
        assert len(cell_0_0.model.agents) == len_before + (num or 1)

    @pytest.mark.parametrize(
        "num, agent, expected_num",
        [
            (1, 0, 0),
            (2, 1, 1),
        ],
    )
    def test_remove(self, cell_0_0: PatchCell, agent, num, expected_num):
        """Test remove cell from everywhere."""
        # arrange
        cell_container = cell_0_0.agents
        actor = cell_container.new(num=num, singleton=True)
        cell_container.remove(agent=actor)

        # assert
        assert actor not in cell_container
        assert actor.at is None
        assert len(cell_container) == expected_num

    def test_remove_all(self, cell_0_0: PatchCell):
        """Test remove all agents from cell."""
        # arrange
        cell_container = cell_0_0.agents
        cell_container.new(num=3)
        # action
        cell_container.remove()
        # assert
        assert len(cell_container) == 0
        assert cell_0_0.agents.is_empty

    def test_add_one_bad_path(self, cell_0_0: PatchCell, cell_0_1: PatchCell):
        """测试不能成功在 Cell 上添加主体的情况：
        1. 同一个主体不能被反复添加到不同的斑块上。
        2. 不能将一个已经存在于其他斑块上的主体添加到当前斑块上。
        """
        # arrange
        actor = cell_0_1.agents.new()
        # action / assert
        # 同一个不能被反复添加
        with pytest.raises(ABSESpyError) as e:
            cell_0_0.agents.add(actor)
            e.match(f"{actor} is on {actor.at} thus cannot be added.")
        # 但是可以先移除位置信息，再添加
        cell_0_1.agents.remove(actor)
        cell_0_0.agents.add(actor)
        assert actor.at is cell_0_0


class TestMaxLength:
    """测试容器的最大长度"""

    @pytest.fixture(name="model_4_agents")
    def model_4_agents(self) -> MainModel:
        """创建一个最大长度为4的模型"""
        return MainModel(max_agents=4)

    @pytest.fixture(name="cell_max_2")
    def cell_max_2(self, model_4_agents: MainModel) -> PatchCell:
        """创建一个最大长度为2的斑块模块"""

        class MaxCell(PatchCell):
            """测试斑块，最大长度为2"""

            max_agents = 2

        module = model_4_agents.nature.create_module(
            how="from_resolution", shape=(2, 2), cell_cls=MaxCell
        )
        return module.cells.random.choice()

    def test_create_bad_path(self, model_4_agents: MainModel):
        """测试创建超过最大长度的主体失败"""
        with pytest.raises(ABSESpyError):
            model_4_agents.agents.new(Actor, 5)

    def test_create_bad_path_in_module(self, cell_max_2: PatchCell):
        """测试在斑块模块中创建超过最大长度的主体失败"""
        with pytest.raises(ABSESpyError):
            cell_max_2.agents.new(Actor, 3)

    def test_add_bad_path(self, cell_max_2: PatchCell):
        """测试添加超过最大长度的主体失败"""
        cell_max_2.model.agents.new(Actor, 3)
        assert len(cell_max_2.model.agents) == 3
        with pytest.raises(ABSESpyError):
            cell_max_2.agents.new(Actor, 2)


class TestSelect:
    """测试选择主体"""

    def test_select_by_attribute(
        self, ternary_m: MainModel, cell_0_0: PatchCell
    ):
        """测试根据属性选择主体"""
        # arrange
        assert cell_0_0.model is ternary_m
        cell_0_0.agents.new(Actor, 3)
        # action
        selected = ternary_m.agents.select("on_earth")
        # assert
        assert len(ternary_m.agents) == 3 + 3
        assert len(selected) == 3

    @pytest.mark.parametrize(
        "selection, agent_type, expected_num",
        [
            (None, "Admin", 3),  # 3个 Admin 类型
            (None, "Farmer", 4),  # 4个 Farmer 类型
            (None, "Actor", 6),  # 6个 Actor 类型，因为都是子类
            ("on_earth", "Actor", 3),  # 3个地球上的 Actor 类型
        ],
    )
    def test_select_by_attribute_and_type(
        self,
        ternary_m: MainModel,
        cell_0_0: PatchCell,
        testing_breeds,
        agent_type,
        expected_num,
        selection,
    ):
        """测试根据属性和类型选择主体"""
        # arrange
        assert cell_0_0.model is ternary_m
        agent_cls = testing_breeds[agent_type]
        cell_0_0.agents.new(agent_cls, 3)
        # action
        selected = ternary_m.agents.select(selection, agent_type=agent_cls)
        # assert
        assert len(selected) == expected_num


class TestCreateGeoAgents:
    """测试创建地理主体"""

    def test_create_geo_agents(self, model: MainModel):
        """测试创建地理主体"""
        # arrange
        data_path = load_data("YR_cities.zip")
        geodf = gpd.read_file(data_path)

        # action
        agents = model.agents.new_from_gdf(
            geodf,
            unique_id="City_ID",
            attrs={"area": "area", "Province_n": "province"},
        )
        agent: Actor = agents.item()
        # assert
        assert agent.geometry
        assert agent.area
        assert agent.province
        assert not hasattr(agent, "Ratio")
        assert agent.alive
        assert agent.on_earth

    def test_create_agents_from_gdf(self, model: MainModel, points_gdf):
        """测试从GeoDataFrame创建主体"""
        # arrange / action
        agents = model.agents.new_from_gdf(
            points_gdf, unique_id="index", agent_cls=Actor
        )
        # assert
        assert len(agents) == len(points_gdf)
