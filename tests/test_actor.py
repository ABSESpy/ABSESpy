#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from typing import Tuple, TypeAlias

import pytest

from abses import MainModel
from abses.actor import Actor
from abses.cells import PatchCell
from abses.nature import PatchModule
from abses.sequences import ActorsList


class TestActor:
    """Test the Actor class."""

    def test_actor_attributes(self):
        """测试主体的属性"""
        model = MainModel()
        actor = Actor(model=model)
        layer = PatchModule.from_resolution(model)

        assert actor.on_earth is False
        assert actor.breed == "Actor"
        pos = (3, 3)
        actor.move.to(layer=layer, pos=pos)
        assert actor.on_earth is True
        assert len(actor.here) == 1
        assert actor.here == ActorsList(model, [actor])

    # def test_actor_selecting(self, model, farmer_cls):
    #     """测试主体的选取"""
    #     actor = Actor(model=model)
    #     actor.test1 = 1
    #     actor.test2 = "testing"
    #     selection = {"test1": 1, "test2": "testing"}
    #     selection2 = "test1 == 1, test2 == testing"
    #     selection3 = "Actor"

    #     assert actor.selecting(selection=selection)
    #     assert actor.selecting(selection=selection2)
    #     assert actor.selecting(selection=selection3)

    #     actor2 = farmer_cls(model=model)
    #     assert actor2.selecting(selection=selection) is False
    #     assert actor2.selecting(selection=selection2) is False
    #     assert actor2.selecting(selection=selection3) is False
