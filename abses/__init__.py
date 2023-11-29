#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
ABSESpy - Agent-based Social-ecological System framework in Python
Copyright (c) 2021-2023 Shuang Song

Documentation: https://absespy.github.io/ABSESpy
Examples: https://absespy.github.io/ABSESpy/tutorial/user_guide/
Source: https://github.com/absespy/ABSESpy
"""

__all__ = [
    "__version__",
    "MainModel",
    "BaseHuman",
    "BaseNature",
    "PatchModule",
    "Actor",
    "Decision",
    "DecisionFactory",
    "ActorsList",
    "AgentsContainer",
    "PatchCell",
    "perception",
]
__version__ = "v0.3.3"

from .actor import Actor, perception
from .container import ActorsList, AgentsContainer
from .decision import Decision, DecisionFactory
from .human import BaseHuman
from .main import MainModel
from .nature import BaseNature, PatchCell, PatchModule
