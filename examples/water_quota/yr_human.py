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


def normalize(arr: np.ndarray) -> np.ndarray:
    """Min-max normalization"""
    min_val = np.min(arr)
    max_val = np.max(arr)

    if max_val == min_val:
        # If all elements are equal (including all zeros),
        # return an array of the same shape with all zeros.
        return np.zeros_like(arr)

    return (arr - min_val) / (max_val - min_val)


def link_groups(graph: nx.Graph, elements: Iterable, p: float = 1) -> nx.Graph:
    """以一定概率将迭代对象里面的要素两两之间建立连边"""
    for comb in list(combinations(elements, 2)):
        if np.random.random() < p:
            graph.add_edge(*comb)
    return graph


def cobb_douglas(parameter: float, times: int):
    """Cobb-Douglas函数"""
    return (1 - parameter) ** times


def lost_reputation(cost, reputation, caught_times, punish_times):
    """损失声誉"""
    # lost reputation because of others' report
    lost = cobb_douglas(reputation, caught_times)
    # not willing to offensively report others
    cost = cobb_douglas(cost, punish_times)
    return cost * lost


class Society(BaseHuman):
    """社会模块"""

    def __init__(self, model, name="human"):
        super().__init__(model, name=name)

    @property
    def farmers(self) -> ActorsList:
        """农民"""
        return self.model.agents.select("Farmer")

    @property
    def defectors(self) -> ActorsList:
        """反对者"""
        return self.farmers.select({"decision": "D"})

    @property
    def cooperators(self) -> ActorsList:
        """合作者"""
        return self.farmers.select({"decision": "C"})

    @time_condition({"month": 12}, when_run=True)
    def step(self):
        """
        每年12月进行一次：
        0. 更新社会属性，包括自己的社交网络
        1. 清空自己的思绪，做决定这个周期要做什么决定 D/C
        2. 如果自己合作，则评价其它朋友的做法，决定是否讨厌他们
        3. 根据自己是否讨厌/是否被人讨厌来更新社会得分
        3. 像表现更好的朋友学习（metric）
        4. 策略变异
        """
        self.update_graph()
        # preparing parameters
        metric = self.params.metric
        mutation = self.params.mutation_probability
        how = self.params.evolve_strategy
        # clear counters
        self.farmers.trigger("clear_mind")
        # like / dislike friends
        self.farmers.trigger("judge_friends")
        # calculate social reputation
        self.update_s()
        # learn from friends
        self.farmers.trigger("change_mind", metric=metric, how=how)
        # mutation strategy
        self.farmers.trigger("mutate_strategy", probability=mutation)
        self.update_e()

    def update_e(self) -> None:
        """更新经济得分"""
        self.farmers.trigger("irrigating")
        costs = np.array(self.farmers.trigger("pumping"))
        # 经济成本
        norm_costs = normalize(costs)
        self.farmers.update("e", 1 - norm_costs)

    def update_s(self):
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
