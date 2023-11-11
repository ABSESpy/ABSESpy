#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

import os
from functools import cached_property
from typing import TYPE_CHECKING, Iterable, Tuple

import numpy as np
import pandas as pd
from hydra import compose, initialize
from pint import UnitRegistry

from abses.actor import Actor, ActorsList
from examples.water_quota.crops import Crop

if TYPE_CHECKING:
    from examples.water_quota.yr_nature import City

ureg = UnitRegistry()  # 注册单位
ureg.define("TMC = 1e8 m ** 3")

with initialize(version_base=None, config_path="."):
    cfg = compose(config_name="config")


class Farmer(Actor):

    """农民"""

    valid_decisions = {
        "C": "Cooperate: compliance with water quota.",
        "D": "Defect: use more water than quota.",
    }

    def __init__(self, *args, city: City = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._crop: Crop = None
        self.city: City = city
        self.quota_min: float = None
        self.quota_max: float = None
        # main point is to distinguish between:
        self.surface_water = 0.0
        self.ground_water = 0.0
        # Social attributes
        self.boldness = self.random.random()
        self.vengefulness = self.random.random()
        self._decision = None
        self.clear_mind()
        self.s: float = 0.0  # score
        self.e: float = 0.0  # score
        self.payoff: float = 0.0  # score

    @property
    def friends(self) -> ActorsList:
        """周围的朋友"""
        return self.linked("friend")

    @property
    def crop(self) -> Crop:
        """该农民种植的作物"""
        return self._crop.name

    @cached_property
    def crop_curve(self) -> pd.Series:
        """该农民种植的作物曲线"""
        values = self._crop.curve(freq="M", full=True).values
        return pd.Series(data=values, index=np.arange(1, 13))

    @crop.setter
    def crop(self, crop: Crop) -> None:
        """设置作物种植类型"""
        if isinstance(crop, str):
            crop_id = cfg.crops_id.get(crop, None)
            path = os.path.join(cfg.db.crops, f"{crop_id}_{crop}.yaml")
            crop = Crop.load_from(path=path)
        if not isinstance(crop, Crop):
            raise TypeError(f"Expect {Crop}, got {type(crop)}.")
        self._crop = crop

    @property
    def Kc(self) -> float:
        """作物的耗水参数"""
        return self.crop_curve.loc[self.time.month]

    @property
    def wui(self) -> float:  # mm/km2/yr * km2 -> mm/yr
        """一整年的用水强度
        单位：mm/km2/yr * km2
        返回一年总用水量（无论什么来源）mm/yr
        """
        return self.city.wui.loc[self.crop]

    @property
    def demands(self) -> float:
        """当月的用水需求：根据作物需要的曲线将WUI平均分配到各个生长月"""
        demands = self.crop_curve / self.crop_curve.sum() * self.wui
        return demands.loc[self.time.month]

    @property
    def deficits(self) -> float:
        """根据当年的降水量和对作物需水量（作物蒸散发）的认识，估计水亏缺"""
        net_deficit = self.loc("etc") - self.loc("prec")
        return 0.0 if net_deficit < 0 else net_deficit / self.params.loss_coef

    @property
    def decision(self) -> str:
        return self._decision

    @decision.setter
    def decision(self, value: str) -> None:
        if value not in self.valid_decisions:
            raise ValueError(f"Invalid decision: {self._decision}.")
        self._decision = value

    def make_decision(self) -> None:
        self.decision = "D" if self.random.random() < self.boldness else "C"

    def clear_mind(self) -> None:
        """忘掉与朋友的间隙，清空自己的思绪，做出决定 D/C"""
        self.dislikes = 0
        self.criticized = 0
        self.make_decision()

    def add_friend_from(self, friends: Iterable[Actor]) -> None:
        """添加朋友"""
        for friend in friends:
            self.link_to(friend, link="friend", mutual=True)

    def mutate_strategy(self, probability: float) -> None:
        """随机更新自己的策略"""
        if self.random.random() > probability:
            return
        if self.random.random() < 0.5:
            self.boldness = self.random.random()
        else:
            self.vengefulness = self.random.random()

    def judge_friends(self) -> int:
        """评价自己的朋友，是不是喜欢它们"""
        # 自己就是违反规则的人，没资格说别人
        if self.decision == "D":
            return self.dislikes
        # judge and report each other
        for friend in self.friends.select({"decision": "D"}):
            if self.vengefulness >= self.random.random():
                self.dislikes += 1
                friend.criticized += 1
        return self.dislikes

    def change_mind(self, metric, how) -> bool:
        """从表现比较好的朋友处学习"""
        better_friends = self.friends.better(metric=metric, than=self)
        if not better_friends:
            return
        elif how == "best":
            friend = better_friends.better(metric=metric)
        elif how == "random":
            friend = better_friends.random_choose()
        self.boldness = friend.boldness
        self.vengefulness = friend.vengefulness

    def decide_water_source(self, quota: float) -> Tuple[float, float, float]:
        """🧑‍🌾根据当月的用水需求决定的用水顺序，优先地表水"""
        # 雨水就满足需求的时候
        if self.demands < quota:
            surface_water = self.demands
            groundwater = 0.0
        # 配额满足需求的时候
        else:
            surface_water = quota
            groundwater = self.demands - quota
        self.surface_water = surface_water
        self.ground_water = groundwater

    def decide_over_withdraw(self) -> float:
        """人有多大胆，地有多大产"""
        if self.decision == "C":
            return 0.0
        return (self.quota_max - self.quota_min) * self.boldness

    def pumping(self):
        """抽水速度 m3/day，这里一个简单实现，只算水的价格"""
        volume = self.ground_water * ureg.mm
        # q_well_m3 = (volume * self.area).to("m**3")
        # num_days = calendar.monthrange(self.time.year, self.time.month)[1]
        # speed = (q_well_m3 / num_days).magnitude
        return self.params.gw_cost * volume.magnitude

    def irrigating(self):
        """灌溉:
        1. 决定多取用多少配额
        2. 根据雨情、配额决定各部分用水比例
        """
        over_quota = self.decide_over_withdraw()
        self.decide_water_source(self.quota_min + over_quota)
