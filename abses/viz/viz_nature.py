#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""Viz natural module.
"""
from __future__ import annotations

import importlib.resources as pkg_resources
from typing import TYPE_CHECKING, Dict, Optional, Type

import fontawesome as fa
import matplotlib.markers as markers
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.path import Path
from matplotlib.textpath import TextToPath

if TYPE_CHECKING:
    from abses.actor import Actor
    from abses.main import MainModel
    from abses.nature import PatchModule

COLOR_BAR = {"fraction": 0.03, "pad": 0.04}

with pkg_resources.path("icons", "fa-regular-400.otf") as fp:
    FONT_AWESOME = FontProperties(fname=str(fp))


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


class _VizNature:
    """Visualize the nature module"""

    def __init__(self, module):
        self.module: PatchModule = module
        self.model: MainModel = module.model

    def _retrieve_marker(self, breed, **kwargs) -> Dict[str, str]:
        breed_cls: Type[Actor] = getattr(self.model, "_breeds")[breed]
        marker_kwargs = breed_cls.viz_attrs(**kwargs)
        marker_kwargs["marker"] = get_marker(marker_kwargs["marker"])
        return marker_kwargs

    def _add_actors(self, breed, ax, **kwargs):
        """Adding"""
        mask = self.module.apply(lambda c: c.agents.has(breed))
        rows, cols = np.where(mask)
        marker_kwargs = self._retrieve_marker(breed, **kwargs)
        ax.scatter(cols, rows, label=breed, **marker_kwargs)
        return ax

    def show(self, attr: Optional[str] = None, **legend_kwargs):
        """Show the nature module"""
        _, ax = plt.subplots()
        if attr is None:
            xda = self.module.xda
            xda.plot(ax=ax, add_colorbar=False, edgecolor="white", alpha=0.8)
        else:
            xda = self.module.get_xarray(attr)
            xda.plot(
                ax=ax, cbar_kwargs=COLOR_BAR, edgecolor="white", alpha=0.8
            )
        for breed in self.model.breeds:
            ax = self._add_actors(breed=breed, ax=ax)
        ax.axes.set_aspect("equal")
        if self.model.breeds:
            ax.legend(**legend_kwargs)
        return ax
