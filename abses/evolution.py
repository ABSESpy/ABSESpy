#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/
import numpy as np


class EvolutionEntry(object):
    def __init__(self, init=None):
        self._lst = list()
        self._now = None
        self.update(init)

    def __repr__(self):
        return f"Evo: < {self.now} >"

    def __len__(self):
        return len(self.previous)

    @property
    def previous(self):
        return tuple(self._lst[:-1])

    @property
    def now(self):
        return self._now

    @now.setter
    def now(self, value):
        self._now = value

    def get(self, memory: int = 0):
        if memory < 0:
            raise ValueError(f"Memory {memory} cannot be smaller than 0.")
        if memory == 0:
            return self.now
        else:
            if len(self.previous) <= memory:
                return self.previous
            else:
                return self.previous[-memory:]

    def update(self, value):
        self._now = value
        if value is not None:
            self._lst.append(value)

    def random(self):
        self.update(np.random.random())
