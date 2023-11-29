#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import pytest

from abses import Actor, MainModel


class TestRandomActorsList:
    @pytest.fixture(name="main")
    def mock_main(self):
        """有随机种子的测试模型"""
        return MainModel(seed=0)

    def test_seed(self, main):
        """测试随机种子是一致的"""
        # arrange
        actors = main.agents.create(Actor, num=3)
        seed = getattr(main, "_seed")
        assert actors.random.seed == seed

        # act
        actor1 = actors.random.choice()

        # assert
        assert actor1 is actors[2]

    def test_link(self, main):
        """测试随机互相连接"""
        # arrange
        actors = main.agents.create(Actor, num=3)

        # act
        linked_combs = actors.random.link("test")

        # assert
        assert len(linked_combs) == 3
        assert actors[1] in actors[0].linked("test")
        assert actors[2] in actors[0].linked("test")
