#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/
from itertools import combinations
from typing import Iterable

import networkx as nx
import numpy as np

from abses.human import BaseHuman
from abses.sequences import ActorsList
from abses.time import time_condition

PROVINCES = [
    "Henan",
    "Neimeng",
    "Ningxia",
    "Qinghai",
    "Shandong",
    "Shanxi",
    "Shaanxi",
    "Gansu",
]


def link_groups(graph: nx.Graph, elements: Iterable, p: float = 1) -> nx.Graph:
    """以一定概率将迭代对象里面的要素两两之间建立连边"""
    for comb in list(combinations(elements, 2)):
        if np.random.random() < p:
            graph.add_edge(*comb)
    return graph


def Cobb_Douglas(parameter: float, times: int):
    return (1 - parameter) ** times


def lost_reputation(cost, reputation, caught_times, punish_times):
    """损失声誉"""
    # lost reputation because of others' report
    lost = Cobb_Douglas(reputation, caught_times)
    # not willing to offensively report others
    cost = Cobb_Douglas(cost, punish_times)
    return cost * lost


class Society(BaseHuman):
    def __init__(self, model, name="human"):
        super().__init__(model, name=name)

    @property
    def farmers(self) -> ActorsList:
        return self.model.agents.select("Farmer")

    @property
    def defectors(self) -> ActorsList:
        return self.farmers.select({"decision": "D"})

    @property
    def cooperators(self) -> ActorsList:
        return self.farmers.select({"decision": "C"})

    @time_condition({"month": 12}, when_run=True)
    def update(self):
        """更新社会属性:
        1. 清空自己的思绪，做决定这个周期要做什么决定 D/C
        2. 如果自己合作，则评价其它朋友的做法，决定是否讨厌他们
        3. 根据自己是否讨厌/是否被人讨厌来更新社会得分
        3. 像表现更好的朋友学习（metric）
        4. 策略变异
        """
        # preparing parameters
        metric = self.params.metric
        mutation = self.params.mutation_probability
        how = self.params.evolve_strategy
        # clear counters
        self.farmers.trigger("clear_mind")
        # like / dislike friends
        self.farmers.trigger("judge_friends")
        # calculate social reputation
        self.update_scores()
        # learn from friends
        self.farmers.trigger("change_mind", metric=metric, how=how)
        # mutation strategy
        self.farmers.trigger("mutate_strategy", probability=mutation)

    def update_scores(self):
        """更新社会得分：
        1. 如果自己被批评得过多，就会觉得不舒服
        2. 如果自己讨厌的朋友太多，也会觉得不舒服
        """
        s_enforcement_cost = self.params.s_enforcement_cost
        s_reputation = self.params.s_reputation
        criticized = self.farmers.array("criticized")
        dislikes = self.farmers.array("dislikes")

        s_scores = lost_reputation(
            cost=s_enforcement_cost,
            reputation=s_reputation,
            caught_times=criticized,
            punish_times=dislikes,
        )
        self.farmers.update("s", s_scores)

    def update_graph(self):
        """更新社会网络"""
        graph = self.graph = nx.Graph()
        for province in PROVINCES:
            cities = self.agents.select(
                {"breed": "City", "Province_n": province}
            )
            hub_agents = []
            for city in cities:
                if not city.farmers:
                    continue
                link_groups(graph, city.farmers, p=self.params.l_p)
                # 每个群体里抽一个“中心节点”，可以和其它的外市主体有交集
                hub_agents.append(city.farmers.random_choose())
            # 这里 Hub 节点怎么选择伙伴？目前用的是全联接
            link_groups(graph, hub_agents, p=self.params.l_p)
            graph.add_edges_from(combinations(hub_agents, 2))
        for farmer in self.farmers:
            friends = list(graph.neighbors(farmer))
            farmer.add_friend_from(friends)
        return graph
