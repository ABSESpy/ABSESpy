#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import numpy as np
import pytest
from shapely.geometry import box

from abses.actor import Actor
from abses.main import MainModel
from abses.nature import BaseNature, PatchCell, PatchModule


class MockActor:
    def __init__(self, geometry=None):
        self.geometry = geometry


def test_patchcell_attachment():
    """测试斑块可以连接到一个主体"""
    cell = PatchCell()
    actor = MockActor()
    cell.link_to(actor, "actor_1")

    assert "actor_1" in cell.links
    assert len(cell.links) == 1
    assert cell.linked("actor_1") == actor

    with pytest.raises(KeyError):
        cell.link_to(actor, "actor_1")

    cell.detach("actor_1")
    assert "actor_1" not in cell.links

    with pytest.raises(KeyError):
        cell.detach("actor_1")


def test_patchmodule_properties():
    """测试一个斑块模块"""
    model = MainModel()
    shape = (6, 5)
    patch_module = PatchModule.from_resolution(model, shape=shape)

    assert patch_module.shape == shape
    assert patch_module.array_cells.shape == shape
    assert isinstance(patch_module.random_positions(5), np.ndarray)

    actor = MockActor()
    patch_module.land_allotment(
        agent=actor, link="land", where=np.ones(shape, dtype=bool)
    )
    assert np.all(patch_module.has_agent() == 1)


@pytest.fixture(name="raster_layer")
def simple_raster_layer():
    """测试一个斑块模块"""
    # Sample setup for RasterLayer (you may need to adjust based on your setup)
    model = MainModel()
    width, height = 10, 10
    layer = PatchModule.from_resolution(model=model, shape=(width, height))
    data = np.random.rand(1, height, width)
    layer.apply_raster(data)
    return layer


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


def test_link_by_geometry(raster_layer):
    """测试每一个斑块可以连接到一个主体"""
    # Define a polygon (for this example, a box)
    geom = box(2, 2, 8, 8)
    agent = MockActor(geom)

    raster_layer.link_by_geometry(agent, "link")

    linked_cells = sum(
        agent is cell.linked("link")
        for cell in raster_layer.array_cells.flatten()
    )

    assert linked_cells > 0, "No cells were linked to the agent!"


def test_batch_link_by_geometry(raster_layer):
    """测试批量将一些斑块连接到某个主体"""
    agents = [MockActor(box(2, 2, 4, 4)), MockActor(box(6, 6, 8, 8))]

    raster_layer.batch_link_by_geometry(agents, "link")

    agents_wrong = [MockActor(box(2, 2, 7, 7)), MockActor(box(6, 6, 8, 8))]
    with pytest.raises(KeyError):
        # 斑块6～7之间将被重复链接，这是不允许的
        raster_layer.batch_link_by_geometry(agents_wrong, "link")
