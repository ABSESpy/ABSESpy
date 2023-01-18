#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/


import numpy as np

from abses.actor import Actor
from abses.container import ActorsList, AgentsContainer
from abses.main import MainModel
from abses.nature import Grid

model = MainModel()
ls1 = ActorsList(model=model)
ls2 = ActorsList(model, 10, Actor)
ls3 = ls2.ids([4, 5])


# def test_agents_list():
#     assert ls1.__repr__() == "<List: 0 Nones>"
#     assert "<List: 10 agents>" == ls2.__repr__()
#     ls1.append(Agent(model=model))  # add 1 agent to ls1
#     ls2.extend(ls1)
#     assert len(ls2) == 11
#     assert ls3.__repr__() == "<List: 2 agents>"


# def test_agents_container():
#     ac1 = AgentsContainer(model, ls3)
#     model._agents = ac1

#     class Sheep(Agent):
#         pass

#     sheep = ActorsList(model, 6, Sheep)
#     ac1.add(sheep)

#     result = ac1.apply(len)  # test apply
#     assert isinstance(result, dict)
#     assert result["sheep"] == len(sheep)
#     assert result["agent"] == len(ls3)

#     class MyGrid(Grid):
#         @apply_agents
#         def add_agents(self, agents=None):
#             super().add_agents(agents)

#     grid = MyGrid(model=model, shape=(50, 50))
#     assert grid.shape == (50, 50)
#     # Add agents form lst 3
#     grid.add_agents(ls3)
#     # those agents already exist in container
#     assert grid.agents.__len__() == len(ls3)
#     for agent in ls3:
#         assert agent in ac1.agent

#     # Thus, no more agents than ac1's agents.
#     grid.add_agents()
#     assert len(grid.agents) == len(ac1)


# def test_better():
#     metric = "s"
#     model = MainModel()
#     f = Farmer(model)
#     farmers = ActorsList(model, 5, Farmer)
#     for i, farmer in enumerate(farmers):
#         farmer.metrics.update(metric, i / 10)

#     f.metrics.update(metric, 0.1)

#     better = farmers.better("s", than=f)
#     assert better.id == [6, 7, 8]
#     assert farmers.better("s", than=None).id == [8]
#     assert farmers.better("s", than=0.05).id == [5, 6, 7, 8]
#     assert better.random_choose() in better
#     for p in [[0, 0, 0], [-1, -1, -1], [-1, 0, 1], [0, 1, 1]]:
#         assert better.random_choose(p=p) in better


# def test_setattr():
#     farmers = ActorsList(model, 5, Farmer)
#     id_arr = farmers.array("id")
#     assert sum(farmers.id) == id_arr.sum()
#     # update agents' attr
#     new_boldness = np.arange(0, 1, 0.2)
#     farmers.update("boldness", new_boldness)
#     assert sum(farmers.boldness) == new_boldness.sum()
#     # update metric
#     metric = "s"
#     farmers.update(metric, np.arange(5) / 10)
#     assert farmers.better("s", than=0.05).id == [5, 6, 7, 8]
