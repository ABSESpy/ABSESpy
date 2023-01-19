#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import networkx as nx

from .container import ActorsList, AgentsContainer
from .modules import CompositeModule


class BaseHuman(CompositeModule):
    def __init__(self, model, name="human"):
        CompositeModule.__init__(self, model, name=name)

    def require(self, attr: str) -> object:
        return self.mediator.transfer_require(self, attr)
