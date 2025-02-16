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
Source: https://github.com/SongshGeoLab/ABSESpy
"""

__all__ = [
    "__version__",
    "MainModel",
    "BaseHuman",
    "BaseNature",
    "PatchModule",
    "Actor",
    "ActorsList",
    "PatchCell",
    "perception",
    "alive_required",
    "time_condition",
    "Experiment",
    "load_data",
]

from importlib.metadata import version

__version__ = f"v{version('abses')}"


from .actor import Actor, alive_required, perception
from .experiment import Experiment
from .human import BaseHuman
from .main import MainModel
from .nature import BaseNature, PatchModule
from .patch import PatchCell
from .sequences import ActorsList
from .time import time_condition
from .tools.data import load_data
