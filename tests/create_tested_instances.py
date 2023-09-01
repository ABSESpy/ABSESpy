#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from typing import Callable, Optional, Union

from agentpy import Model

from abses.actor import Actor
from abses.bases import Mediator, Notice
from abses.main import MainModel
from abses.tools.read_files import read_yaml

world = read_yaml("config/world.yaml")


class Farmer(Actor):
    pass


class Admin(Actor):
    pass


def noticeable_model():
    class MyModel(Model, Notice):
        def __init__(self):
            Model.__init__(self)
            Notice.__init__(self)
            self.mediator = None
            self.params = {}

    model = MyModel()
    model.a = 1
    model.glob_vars = "a"
    return model
