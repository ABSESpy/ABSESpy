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
from abses._bases.errors import ABSESpyError
from abses.actor import Actor
from abses.cells import PatchCell
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

    @pytest.mark.parametrize(
        "ticks, expected",
        [
            (1, 1),
            (3, 3),
        ],
    )
    def test_actor_age(self, model: MainModel, ticks, expected):
        """测试主体的年龄计算"""
        # arrange
        actor = model.agents.new(Actor, singleton=True)
        assert actor.age() == 0
        model.time.go(ticks=ticks)
        # act
        age = actor.age()
        # assert
        assert age == expected

    def test_attributes(self, model: MainModel):
        """测试主体的属性"""
        # arrange / act
        actor = model.agents.new(Actor, singleton=True)

        # act / assert
        assert actor.on_earth is False
        assert actor.breed == "Actor"
        assert actor.at is None

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
        assert not actor1.age()


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
    """测试获取值。"""

    @pytest.mark.parametrize(
        "target, expected",
        [
            ("actor", 3),  # 直接指定 target
            (None, 3),  # 未指定 target,属性存在
            ("cell", 2),  # 直接指定 target
        ],
    )
    def test_get_happy_path(self, cell_0_0: PatchCell, target, expected):
        """测试正常获取值的情况。"""
        # 准备
        actor = cell_0_0.agents.new(Actor, singleton=True)
        cell_0_0.test = 2
        actor.test = 3
        # 执行
        value = actor.get("test", target=target)
        # 断言
        assert value == expected

    @pytest.mark.parametrize(
        "target, error, msg",
        [
            ("actor", AttributeError, "nonexistent"),  # target_is_me
            (
                "cell",
                AttributeError,
                "no attribute 'nonexistent'",
            ),  # 明确指定 target
            ("not_a_target", ABSESpyError, "Unknown target"),  # 未知 target
            (
                None,
                AttributeError,
                "Neither.*nor.*has attribute",
            ),  # 未指定 target,属性不存在
        ],
    )
    def test_get_wrong(self, cell_0_0: PatchCell, target, error, msg):
        """测试获取值时的错误情况。"""
        # 准备
        actor = cell_0_0.agents.new(Actor, singleton=True)
        actor.test = 1
        cell_0_0.test = 2
        # 执行和断言
        with pytest.raises(error, match=msg):
            actor.get("nonexistent", target=target)


class TestSettingValues:
    """测试设置值。"""

    @pytest.mark.parametrize(
        "target, value, new",
        [
            ("actor", 1, False),
            (None, "testing text", False),
            ("actor", ["test", "test1", "test2"], False),
            ("actor", 100, True),
        ],
    )
    def test_set_happy_path(self, cell_0_0: PatchCell, value, target, new):
        """测试正常设置值的情况。"""
        # 准备
        actor = cell_0_0.agents.new(Actor, singleton=True)
        if not new:
            actor.test = 0
        # 执行
        actor.set(attr="test", value=value, target=target, new=new)
        # 断言
        assert actor.get(attr="test", target=target) == value

    @pytest.mark.parametrize(
        "attr, target, value, new, error, msg",
        [
            (
                "test2",
                None,
                1,
                False,
                AttributeError,
                "Neither.*nor.*has attribute 'test2'",
            ),
            ("test2", "cell", 1, False, AttributeError, "not found"),
            ("test2", "actor", 1, False, AttributeError, "not found"),
            ("test", "not_a_target", 1, False, ABSESpyError, "Unknown target"),
            ("_test", "actor", 1, True, AttributeError, "protected"),
        ],
    )
    def test_set_wrong(
        self, cell_0_0: PatchCell, attr, target, value, new, error, msg
    ):
        """测试设置值时的错误情况。"""
        # 准备
        actor = cell_0_0.agents.new(Actor, singleton=True)
        actor.test = 1
        cell_0_0.test = 2
        # 执行和断言
        with pytest.raises(error, match=msg):
            actor.set(attr=attr, value=value, target=target, new=new)

    def test_set_new_attribute(self, cell_0_0: PatchCell):
        """测试设置新属性。"""
        # 准备
        actor = cell_0_0.agents.new(Actor, singleton=True)
        # 执行
        actor.set(attr="new_attr", value=100, new=True)
        # 断言
        assert actor.get("new_attr") == 100

    def test_set_existing_attribute_without_new(self, cell_0_0: PatchCell):
        """测试在不使用new参数的情况下设置已存在的属性。"""
        # 准备
        actor = cell_0_0.agents.new(Actor, singleton=True)
        actor.existing_attr = 50
        # 执行
        actor.set(attr="existing_attr", value=100)
        # 断言
        assert actor.get("existing_attr") == 100

    def test_set_on_cell(self, cell_0_0: PatchCell):
        """测试在cell上设置属性。"""
        # 准备
        actor = cell_0_0.agents.new(Actor, singleton=True)
        # 执行
        actor.set(attr="cell_attr", value=200, target="cell", new=True)
        # 断言
        assert cell_0_0.get("cell_attr") == 200
