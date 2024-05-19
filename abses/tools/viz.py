#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""Some tools for better viz.
"""
import importlib.resources as pkg_resources

import fontawesome as fa
import matplotlib.markers as markers
import numpy as np
from matplotlib.font_manager import FontProperties
from matplotlib.path import Path
from matplotlib.textpath import TextToPath

COLOR_BAR = {"fraction": 0.03, "pad": 0.04}

FONT = pkg_resources.files("icons") / "fa-regular-400.otf"
FONT_AWESOME = FontProperties(fname=str(FONT))


# https://stackoverflow.com/questions/52902086/how-to-use-font-awesome-symbol-as-marker-in-matplotlib
def get_marker(symbol: str) -> Path:
    """Returns Font Awesome marker."""
    if symbol in markers.MarkerStyle.markers:
        return symbol
    symbol = fa.icons.get(symbol)
    if not symbol:
        raise KeyError(f"Could not find {symbol} in marker style.")
    v, codes = TextToPath().get_text_path(FONT_AWESOME, symbol)
    v = np.array(v)
    mean = np.mean([np.max(v, axis=0), np.min(v, axis=0)], axis=0)
    return Path(v - mean, codes, closed=False)
