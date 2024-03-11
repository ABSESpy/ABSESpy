#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
测试行动者，包括
1. 新建的行动者拥有正确的属性；
2. 移动到某个斑块上
3. 死亡
4. 获取属性值（自己或所在斑块）
5. 设置属性值（自己或所在斑块）
"""

import pytest

from abses import MainModel
from abses.actor import Actor
from abses.cells import PatchCell
from abses.nature import PatchModule


class TestActor:
    """Test the Actor class."""

    def test_attributes(self, model: MainModel):
        """测试主体的属性"""
        # arrange / act
        actor = model.agents.create(Actor, singleton=True)

        # act / assert
        assert actor.on_earth is False
        assert actor.breed == "Actor"
        assert actor.at is None
        assert actor.unique_id == 1

    def test_movements(
        self, model: MainModel, module: PatchModule, cell_0_0: PatchCell
    ):
        """Test moving"""
        # arrange
        actor = model.agents.create(Actor, singleton=True)
        # act
        pos = (0, 0)
        actor.move.to(layer=module, pos=pos)
        # assert
        assert actor.on_earth is True
        assert len(actor.at.agents) == 1
        assert actor.at is cell_0_0
        assert actor.layer is module

    def test_die(self, model: MainModel, cell_0_0: PatchCell):
        """Test die"""
        # arrange
        actor1 = model.agents.create(Actor, num=1, singleton=True)
        actor2 = cell_0_0.agents.create(Actor, singleton=True)
        # act
        actor1.die()
        actor2.die()
        # assert
        assert actor1 not in model.agents
        assert actor2 not in model.agents
        assert len(model.agents) == 0

    @pytest.mark.parametrize(
        "attr, target, expected",
        [
            ("test2", None, 3),
            ("test2", "self", 3),
            ("test2", "at", 2),
        ],
    )
    def test_get(self, cell_0_0: PatchCell, attr, target, expected):
        """Test getting values."""
        # arrange
        actor = cell_0_0.agents.create(Actor, singleton=True)
        cell_0_0.test1 = 1
        cell_0_0.test2 = 2
        actor.test2 = 3
        # act
        value = actor.get(attr=attr, target=target)
        # assert
        assert value == expected

    @pytest.mark.parametrize(
        "attr, target, value",
        [
            ("test1", "self", 1),
            ("test2", "me", "testing text"),
            ("test", "actor", ["test", "test1", "test2"]),
        ],
    )
    def test_set(self, cell_0_0: PatchCell, attr, value, target):
        """Test setting values."""
        # arrange
        actor = cell_0_0.agents.create(Actor, singleton=True)
        # act
        actor.set(attr=attr, value=value, target=target)
        # assert
        assert getattr(actor, attr) == value

    @pytest.mark.parametrize(
        "attr, target, value",
        [
            ("test1", "at", 1),
            ("test1", "nature", 1),
            ("test1", "world", 1),
        ],
    )
    def test_set_cell(self, cell_0_0: PatchCell, attr, value, target):
        """Test setting values."""
        # arrange
        actor = cell_0_0.agents.create(Actor, singleton=True)
        # act
        actor.set(attr=attr, value=value, target=target)
        # assert
        assert getattr(cell_0_0, attr) == value
