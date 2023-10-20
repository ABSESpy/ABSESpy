#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from typing import Tuple, TypeAlias

import networkx as nx
import pytest

from abses import MainModel
from abses.actor import Actor
from abses.cells import PatchCell
from abses.nature import PatchModule
from abses.sequences import ActorsList


def test_actor_attributes():
    """测试主体的属性"""
    model = MainModel()
    actor = Actor(model=model)
    layer = PatchModule.from_resolution(model)

    assert actor.on_earth is False
    assert actor.breed == "Actor"
    pos = (3, 3)
    actor.put_on_layer(layer=layer, pos=pos)
    assert actor.on_earth is True
    assert actor.pos == pos
    assert len(actor.here) == 1
    assert actor.here == ActorsList(model, [actor])


def test_actor_selecting():
    """测试主体的选取"""
    model = MainModel()
    actor = Actor(model=model)
    actor.test1 = 1
    actor.test2 = "testing"
    selection = {"test1": 1, "test2": "testing"}
    selection2 = "test1 == 1, test2 == testing"
    selection3 = "Actor"

    assert actor.selecting(selection=selection)
    assert actor.selecting(selection=selection2)
    assert actor.selecting(selection=selection3)

    class Farmer(Actor):
        """测试用"""

        def __init__(self, model, observer: bool = True) -> None:
            super().__init__(model, observer)
            self.test2 = 2
            self.test2 = "testing"

    actor2 = Farmer(model=model)
    assert actor2.selecting(selection=selection) is False
    assert actor2.selecting(selection=selection2) is False
    assert actor2.selecting(selection=selection3) is False


def test_actor_rule():
    """测试行动者会按照预设的规则进行行动"""
    model = MainModel()
    actor = Actor(model=model)
    assert actor.on_earth is False
    actor.put_on_layer(layer=PatchModule.from_resolution(model), pos=(1, 1))

    selection = {"test1": 1, "test2": "testing"}

    # 当满足选择条件时，就会自动前进到目标位置（3，3）
    actor.rule(
        when=selection, then="move_to", position=(3, 3), disposable=True
    )
    assert actor.selecting(selection) is False

    actor.test1 = 1
    assert actor.selecting(selection) is False

    actor.test2 = "testing"
    assert actor.selecting(selection) is True
    assert actor.on_earth is True
    assert actor.pos == (3, 3)


Links: TypeAlias = Tuple[MainModel, PatchCell, PatchCell, Actor, Actor]


@pytest.fixture(name="links")
def test_links() -> Links:
    """测试主体的连接"""
    model = MainModel()
    test = model.nature.create_module(
        how="from_resolution", name="test", shape=(1, 2)
    )
    cell_1 = test.cells[0][0]
    cell_2 = test.cells[1][0]
    agent_1 = Actor(model=model)
    agent_2 = Actor(model=model)
    return model, cell_1, cell_2, agent_1, agent_2


def test_linked(links: Links):
    """测试主体的连接"""
    model, cell_1, cell_2, agent_1, agent_2 = links
    agent_1.link_to(cell_1, "land")
    agent_2.link_to(cell_2, "land")
    agent_1.link_to(agent_2, link="friend")

    assert cell_1 in agent_1.linked("land")
    assert cell_2 in agent_2.linked("land")
    assert agent_1 in agent_2.linked("friend")
    assert agent_2 in agent_1.linked("friend")

    friends = model.human.get_graph("friend")
    lands = model.human.get_graph("land")
    assert model.human.links
    assert len(nx.degree(friends)) == 2
    assert len(nx.degree(lands)) == 4
