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

from abses import MainModel, alive_required
from abses.actor import Actor
from abses.cells import PatchCell
from abses.errors import ABSESpyError
from abses.nature import PatchModule


class DeadMan(Actor):
    """测试用，另一个类别的主体"""

    def __repr__(self) -> str:
        return "I'm alive." if self.alive else "I'm dead."

    def die_once(self) -> None:
        """死一次"""
        self.die()

    @alive_required
    def speak(self) -> str:
        """如果活着，才能说话"""
        return repr(self)

    def speak_bad(self) -> str:
        """如果活着，才能说话"""
        return f"{repr(self)} but, I'm speaking! Fuck."


class TestActor:
    """Test the Actor class."""

    def test_attributes(self, model: MainModel):
        """测试主体的属性"""
        # arrange / act
        actor = model.agents.new(Actor, singleton=True)

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
        actor = model.agents.new(Actor, singleton=True)
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
        actor1 = model.agents.new(Actor, num=1, singleton=True)
        actor2 = cell_0_0.agents.new(Actor, singleton=True)
        # act
        actor1.die()
        actor2.die()
        # assert
        assert actor1 not in model.agents
        assert actor2 not in model.agents
        assert len(model.agents) == 0

    @pytest.mark.parametrize(
        "attr, target, value",
        [
            ("test1", "cell", 1),
            ("test1", None, 1),
        ],
    )
    def test_set_cell(self, cell_0_0: PatchCell, attr, value, target):
        """Test setting values."""
        # arrange
        cell_0_0.test1 = 0
        actor = cell_0_0.agents.new(Actor, singleton=True)
        # act
        actor.set(attr=attr, value=value, target=target)
        # assert
        assert getattr(cell_0_0, attr) == value


class TestCustomizedActor:
    """Test the customized Actor class."""

    def test_die(self, model: MainModel):
        """Test die"""
        # arrange
        actor = model.agents.new(Actor, singleton=True)
        # act
        actor.die()
        actor.die()
        # assert
        assert actor not in model.agents
        assert actor.get() is None

    def test_city_die(self, model: MainModel):
        """Test die"""
        # arrange
        man: DeadMan = model.agents.new(DeadMan, singleton=True)
        # act
        man.die_once()
        # assert
        assert man.speak() is None, "Dead man speaks! Crazy."
        assert man.get() is None
        assert isinstance(man.speak_bad(), str)


class TestGettingValues:
    """Test getting values."""

    @pytest.mark.parametrize(
        "attr, target, expected",
        [
            ("test2", None, 3),
            ("test2", "actor", 3),
            ("test2", "cell", 2),
        ],
    )
    def test_get_happy_path(self, cell_0_0: PatchCell, attr, target, expected):
        """Test getting values."""
        # arrange
        actor = cell_0_0.agents.new(Actor, singleton=True)
        cell_0_0.test2 = 2
        actor.test2 = 3
        # act
        value = actor.get(attr=attr, target=target)
        # assert
        assert value == expected

    @pytest.mark.parametrize(
        "attr, target, error, msg",
        [
            ("test2", None, AttributeError, "no attribute 'test2'"),
            ("test2", "cell", AttributeError, "no attribute 'test2'"),
            ("test2", "actor", AttributeError, "no attribute 'test2'"),
            (
                "test",
                "not_a_target",
                AssertionError,
                "already has attr 'test'",
            ),
            ("test2", "not_a_target", ABSESpyError, "Unknown target"),
            ("test2", "linking", AttributeError, "no attribute 'test2'"),
        ],
    )
    def test_get_wrong(self, cell_0_0: PatchCell, attr, target, error, msg):
        """Testing getting values in batch.
        When the target is None, the agent itself is the target.
        """
        # arrange
        actor1 = cell_0_0.agents.new(Actor, singleton=True)
        actor1.link.to(cell_0_0, "linking")
        actor1.test = 1
        cell_0_0.test = 2
        # act / assert
        with pytest.raises(error, match=msg):
            actor1.get(attr, target=target)


class TestSettingValues:
    """Test setting values."""

    @pytest.mark.parametrize(
        "attr, target, value",
        [
            ("test", "actor", 1),
            ("test", None, "testing text"),
            ("test", "actor", ["test", "test1", "test2"]),
        ],
    )
    def test_set_happy_path(self, cell_0_0: PatchCell, attr, value, target):
        """Test setting values."""
        # arrange
        actor = cell_0_0.agents.new(Actor, singleton=True)
        actor.test = 0
        # act
        actor.set(attr=attr, value=value, target=target)
        # assert
        assert getattr(actor, attr) == value
