#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from typing import Tuple

import geopandas as gpd
import numpy as np
import pytest
from shapely.geometry import Point, box

from abses.actor import Actor
from abses.cells import raster_attribute
from abses.errors import ABSESpyError
from abses.links import LinkContainer, LinkNode
from abses.main import MainModel
from abses.nature import PatchCell, PatchModule


class MockActor(LinkNode):
    """测试行动者"""

    def __init__(self, geometry=None):
        super().__init__()
        self.geometry = geometry
        self.test = 1
        self.container = LinkContainer()


class MockPatchCell(PatchCell):
    """测试斑块"""

    @raster_attribute
    def x(self) -> int:
        return 1

    @raster_attribute
    def y(self) -> int:
        return 2


def test_setup_attributes():
    """测试斑块提取属性"""
    instance = MockPatchCell()
    properties = instance.__attribute_properties__()
    assert isinstance(properties, set)
    assert instance.x == 1
    assert instance.y == 2
    assert "x" in properties
    assert "y" in properties
    model = MainModel()
    shape = (6, 5)
    patch_module = PatchModule.from_resolution(
        model, shape=shape, cell_cls=MockPatchCell
    )
    assert "x" in patch_module.attributes
    assert "y" in patch_module.attributes
    assert len(patch_module.attributes) == 2
    assert patch_module.get_raster("x").sum() == 30


def test_patch_cell_attachment():
    """测试斑块可以连接到一个主体"""
    cell = LinkNode()
    cell.container = LinkContainer()
    actor = MockActor()
    cell.link_to(actor, "actor_1")

    assert "actor_1" in cell.links
    assert len(cell.links) == 1
    assert actor in cell.linked("actor_1")


def test_patch_module_properties():
    """测试一个斑块模块"""
    model = MainModel()
    shape = (6, 5)
    patch_module = PatchModule.from_resolution(model, shape=shape)

    assert patch_module.shape2d == shape
    assert patch_module.shape3d == (1, *shape)
    assert patch_module.array_cells.shape == shape
    assert isinstance(patch_module.random_positions(5), np.ndarray)
    coords = patch_module.coords
    assert "x" in coords and "y" in coords
    assert len(coords["x"]) == 5 and len(coords["y"]) == 6

    actor = MockActor()
    patch_module.land_allotment(
        agent=actor, link="land", where=np.ones(shape, dtype=bool)
    )
    assert np.all(patch_module.has_agent(link="land") == 1)


@pytest.fixture(name="raster_layer")
def simple_raster_layer() -> PatchModule:
    """测试一个斑块模块"""
    # Sample setup for RasterLayer (you may need to adjust based on your setup)
    model = MainModel()
    width, height = 10, 10
    layer = PatchModule.from_resolution(model=model, shape=(width, height))
    data = np.random.rand(1, height, width)
    layer.apply_raster(data, "test_1")
    return layer


def test_get_dataarray(raster_layer: PatchModule):
    """测试获取数据数组"""
    data = np.random.random(raster_layer.shape3d)
    raster_layer.apply_raster(data, "test_2")
    data = np.random.random(raster_layer.shape3d)
    raster_layer.apply_raster(data, "test_3")
    dataarray_2d = raster_layer.get_xarray("test_2")
    assert dataarray_2d.shape == raster_layer.shape2d
    dataarray_3d = raster_layer.get_xarray()
    assert dataarray_3d.shape == (3, *raster_layer.shape2d)


def test_geometric_cells(raster_layer):
    """测试几何搜索"""
    # Define a geometry (for this example, a box)
    geom = box(2, 2, 8, 8)

    # Get cells intersecting with the geometry
    cells = raster_layer.geometric_cells(geom)

    # Check if each cell's position is within the geometry
    for cell in cells:
        x, y = cell.pos
        assert geom.contains(
            box(x, y, x + 1, y + 1)
        ), f"Cell at {x}, {y} is not within the geometry!"


@pytest.fixture(name="linked_raster_layer")
def simple_linked_raster_layer(raster_layer):
    """测试每一个斑块可以连接到一个主体"""
    # Define a polygon (for this example, a box)
    geom = box(2, 2, 8, 8)
    agent = Actor(model=raster_layer.model, geometry=geom)
    agent.test = 1
    raster_layer.link_by_geometry(agent, "link")
    return agent, raster_layer


def test_link_by_geometry(linked_raster_layer):
    """测试每一个斑块可以连接到一个主体"""
    agent, raster_layer = linked_raster_layer
    cells = agent.linked("link")
    arr = raster_layer.linked_attr(attr="test", link="link")
    assert np.nansum(arr) == len(cells)


def test_batch_link_by_geometry(raster_layer):
    """测试批量将一些斑块连接到某个主体"""
    agents = [MockActor(box(2, 2, 4, 4)), MockActor(box(6, 6, 8, 8))]

    raster_layer.batch_link_by_geometry(agents, "link")
    arr = raster_layer.linked_attr(attr="test", link="link")
    assert np.nansum(arr) == 8

    overlapped = [MockActor(box(2, 2, 7, 7)), MockActor(box(6, 6, 8, 8))]
    raster_layer.batch_link_by_geometry(overlapped, "link")
    with pytest.raises(ValueError):
        arr2 = raster_layer.linked_attr(attr="test", link="link")
    arr2 = raster_layer.linked_attr(attr="test", link="link", how="random")
    assert np.nansum(arr2) == 25 + 4 - 1  # one agent is overlapped


def test_read_attrs_from_linked_agent(linked_raster_layer):
    """测试从相连接的主体中读取属性"""
    _, raster_layer = linked_raster_layer
    array = raster_layer.linked_attr("test", link="link")
    assert isinstance(array, np.ndarray)
    assert array.shape == raster_layer.shape2d
    assert np.nansum(array) == 36

    # 测试某个主体是否被正确链接并读取
    linked_cell = raster_layer.array_cells[4][4]
    not_linked_cell = raster_layer.array_cells[1][1]

    assert linked_cell.linked_attr("test", link="link") == 1
    with pytest.raises(ValueError):
        not_linked_cell.linked_attr("test", link="link")

    with pytest.raises(AttributeError):
        linked_cell.linked_attr("not_a_attr", link="link")


def test_major_layer(raster_layer):
    """测试选择主要图层"""
    layer = raster_layer
    model = layer.model
    assert model.nature.total_bounds is None
    model.nature.major_layer = layer
    assert model.nature.total_bounds is layer.total_bounds


def test_create_agents_from_gdf():
    """测试从GeoDataFrame创建主体"""
    # Step 1: Create a sample geopandas.GeoDataFrame with some dummy data
    data = {
        "name": ["agent_1", "agent_2", "agent_3"],
        "age": [25, 30, 35],
        "geometry": [Point(0, 0), Point(1, 1), Point(2, 2)],
    }
    gdf = gpd.GeoDataFrame(data, crs="epsg:4326")

    # Initialize BaseNature instance
    model = MainModel()
    nature = model.nature

    # Step 2: Use the create_agents_from_gdf method
    agents = nature.create_agents_from_gdf(
        gdf, unique_id="name", agent_cls=Actor
    )

    # Step 3: Assert number of created agents
    assert len(agents) == len(gdf)

    # Step 4: Check each agent's attributes and geometry
    for idx, agent in enumerate(agents):
        assert agent.unique_id == gdf.iloc[idx]["name"]
        assert agent.age == gdf.iloc[idx]["age"]
        assert agent.geometry == gdf.iloc[idx]["geometry"]


def test_copy_layer(raster_layer: PatchModule):
    """测试复制图层"""
    layer = raster_layer
    layer2 = layer.model.nature.create_module(
        PatchModule, how="copy_layer", layer=layer
    )
    assert layer.shape2d == layer2.shape2d


def test_loc():
    """测试定位"""
    model = MainModel()
    width, height = 2, 3
    layer = PatchModule.from_resolution(model=model, shape=(height, width))
    data = np.arange(6).reshape(1, 3, 2)
    layer.apply_raster(data, "test")

    agent = Actor(model=model)
    agent.put_on_layer(layer, (0, 0))
    assert agent.loc("test") == 4


@pytest.fixture(name="cells")
def my_cells() -> Tuple[PatchCell]:
    """模拟两个斑块"""
    model = MainModel()
    test = model.nature.create_module(
        how="from_resolution", name="test", shape=(1, 2)
    )
    cell_1 = test.cells[0][0]
    cell_2 = test.cells[1][0]
    return cell_1, cell_2


class Dog(Actor):
    """a dog for testing"""


@pytest.fixture(name="agents")
def my_agents() -> Tuple[Dog]:
    """模拟两个主体"""
    model = MainModel()
    agent_1 = Dog(model=model)
    agent_2 = Dog(model=model)
    return agent_1, agent_2


def test_add_agent(cells, agents):
    """测试添加主体"""
    agent1, agent2 = agents
    assert agent1.breed == agent2.breed == "Dog"
    cell1, cell2 = cells
    # Test adding the first agent of a breed
    agent1.put_on(cell1)
    with pytest.raises(ABSESpyError):
        cell2.add(agent1)
    assert agent1 in cell1.agents

    cell1.add(agent2)
    assert len(cell1.agents) == 2


def test_remove_agent(agents, cells):
    """测试移除主体"""
    agent1, agent2 = agents
    cell1, cell2 = cells
    # Add some initial agents
    agent1.put_on(cell1)
    agent2.put_on(cell2)

    # Test removing one agent
    cell1.remove(agent1)
    assert "Dog" not in cell1._agents
    assert "Dog" in cell2._agents
    assert agent1 not in cell1.agents

    agent2.put_on(cell1)
    assert agent2 in cell1.agents
    assert agent2 not in cell2.agents
    agent2.put_on(cell1)
    assert not agent1.on_earth
    assert agent2.on_earth
    agent1.put_on(cell1)
    assert len(cell1.agents) == 2
    agent2.put_on(cell2)
