#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from abses.actor import Actor


class Farmer(Actor):
    """测试用，另一个类别的主体"""

    def __init__(self, model, observer: bool = True) -> None:
        super().__init__(model, observer)
        self.metric = 0.1


class Admin(Actor):
    """测试用，另一个类别的主体"""
