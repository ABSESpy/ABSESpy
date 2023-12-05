#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import numpy as np
import pytest

from abses import Actor, MainModel
from abses.errors import ABSESpyError


class TestRandomActorsList:
    """测试主体列表的随机"""

    @pytest.fixture(name="main")
    def mock_main(self):
        """有随机种子的测试模型"""
        return MainModel(seed=0)

    def test_seed(self, main: MainModel):
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

    @pytest.mark.parametrize(
        "actors_num, p, expected_p",
        [
            (2, [0, 0], [0.5, 0.5]),
            (2, [-1, 0], [0.5, 0.5]),
            (2, [np.nan, np.nan], [0.5, 0.5]),
            (2, [np.nan, np.nan], [0.5, 0.5]),
            (2, [np.nan, 3], [0, 1]),
            (1, [np.nan], [1]),
            (1, [-1], [1]),
            (2, [3, 2], [0.6, 0.4]),
        ],
        ids=[
            ("Zero values"),
            ("Negative-Zero values"),
            ("Nan values"),
            ("Nan-negative values"),
            ("Nan-positive values"),
            ("One NaN value"),
            ("One negative value"),
            ("Normal values"),
        ],
    )
    def test_clean_p(self, main: MainModel, actors_num, p, expected_p):
        """测试清理概率"""
        # arrange
        agents = main.agents.create(Actor, num=actors_num)
        agents.update("test", p)

        # act
        possibilities = agents.random.clean_p(prob="test")

        # assert
        assert np.allclose(possibilities, expected_p)

    @pytest.mark.parametrize(
        "num, size, replace",
        [
            (0, 2, True),
            (1, 2, False),
        ],
    )
    def test_bad_choose(self, main: MainModel, num, size, replace):
        """测试不能选取的一些情况"""
        agents = main.agents.create(Actor, num=num)

        # act / assert
        with pytest.raises(ABSESpyError):
            agents.random.choice(size=size, replace=replace)

    @pytest.mark.parametrize(
        "size, p, replace, expected",
        [
            (2, [0.1, 0.4], False, [0, 1]),
            (2, [np.nan, 1], True, [1, 1]),
            (1, [np.nan, 1], False, [1]),
        ],
        ids=[
            "choose all two",
            "expected two, but only one to choose",
            "only one to choose",
        ],
    )
    def test_random_choose(self, main: MainModel, size, p, replace, expected):
        """测试从列表中随机抽取"""
        # arrange
        agents = main.agents.create(Actor, num=2)

        # act
        chosen = agents.random.choice(
            size=size, prob=p, as_list=True, replace=replace
        )

        # assert
        assert chosen == [agents[i] for i in expected]

    @pytest.mark.parametrize(
        "p, expected",
        [
            ([0.5, 0.1], 0),
            ([np.nan, 1], 1),
        ],
        ids=[
            "choose the first one",
            "choose the second one",
        ],
    )
    def test_random_choose_one(self, main: MainModel, p, expected):
        """测试从列表中随机抽取"""
        # arrange
        agents = main.agents.create(Actor, num=2)

        # act
        chosen = agents.random.choice(prob=p, as_list=False)

        # assert
        assert isinstance(chosen, Actor)
        assert chosen is agents[expected]
