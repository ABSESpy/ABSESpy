#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""Handling some example datasets.
"""
from importlib import resources
from pathlib import Path
from typing import Literal

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias


DATA_LIST = [
    "farmland.tif",
    "precipitation.nc",
    "irr_lands.csv",
    "YR_cities.zip",
]
DataChoices: TypeAlias = Literal[
    "farmland.tif",
    "precipitation.nc",
    "irr_lands.csv",
    "YR_cities.zip",
]


def load_data(filename: DataChoices) -> Path:
    """Load data from the package."""
    if filename not in DATA_LIST:
        raise FileNotFoundError(
            f"Cannot load data {filename},"
            f"Example Datasets include: {DATA_LIST}."
        )
    return Path(str(resources.files("data") / filename))
