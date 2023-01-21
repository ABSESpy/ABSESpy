#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
ABSESpy - Agent-based Social-ecological System framework in Python
Copyright (c) 2021-2023 Shuang Song

Documentation: https://agentpy.readthedocs.io/
Examples: https://agentpy.readthedocs.io/en/latest/model_library.html
Source: https://github.com/JoelForamitti/agentpy
"""

__all__ = [
    "__version__",
    "MainModel",
    "BaseHuman",
    "BaseNature",
    "HumanModule",
    "PatchModule",
    "Agent",
    "ActorsList",
    "AgentsContainer" "MyExperiment",
]
__version__ = "v0.0.1"

from .actor import Actor
from .container import ActorsList, AgentsContainer
from .human import BaseHuman, HumanModule
from .main import MainModel
from .nature import BaseNature, PatchModule
from .objects import *
