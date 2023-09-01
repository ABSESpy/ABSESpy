#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import numpy as np
import pytest

from abses.actor import Actor
from abses.main import MainModel
from abses.nature import BaseNature, PatchCell, PatchModule

from .create_tested_instances import simple_main_model


class MockActor:
    """用户"""


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
