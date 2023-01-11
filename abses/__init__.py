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
    "BaseAgentList",
    "AgentsContainer" "MyExperiment",
]
__version__ = "0.0.1"

from .agents import Actor
from .container import AgentsContainer, BaseAgentList
from .human import BaseHuman
from .main import MainModel
from .modules import HumanModule, PatchModule
from .nature import BaseNature
from .objects import *
