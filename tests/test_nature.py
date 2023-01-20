#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import numpy as np

from abses.actor import Actor
from abses.nature import BaseNature

from .create_tested_instances import simple_main_model


def test_nature_positions():
    model = simple_main_model(test_nature_positions)
    nature = model.nature
    actors = model.agents.create(Actor, 5)
    assert nature.shape == (9, 9)
    zeros = np.zeros(nature.shape, bool)
    zeros[0, 0] = True
    try:
        nature.random_positions(k=5, where=zeros, replace=False)
    except Exception as e:
        assert "larger" in str(e)
    positions_replace = nature.random_positions(k=5, where=zeros, replace=True)
    model.nature.add_agents(actors, positions_replace)
    assert (actors.pos == (0, 0)).all()
