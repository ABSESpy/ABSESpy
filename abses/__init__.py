#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
ABSESpy - Agent-based Social-ecological System framework in Python
Copyright (c) 2021-2023 Shuang Song

Documentation: https://songshgeo.github.io/ABSESpy
Examples: https://songshgeo.github.io/ABSESpy/tutorial/user_guide/
Source: https://github.com/SongshGeo/ABSESpy
"""

__all__ = [
    "__version__",
    "MainModel",
    "BaseHuman",
    "BaseNature",
    "HumanModule",
    "PatchModule",
    "Actor",
    "ActorsList",
    "AgentsContainer",
    "link_to",
    "perception",
    # "MyExperiment",
]
__version__ = "v0.1.3"

from .actor import Actor, link_to, perception
from .container import ActorsList, AgentsContainer
from .human import BaseHuman, HumanModule
from .main import MainModel
from .nature import BaseNature, PatchModule
from .objects import *
