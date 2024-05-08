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
from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional, Type, cast

import fontawesome as fa
import matplotlib.markers as markers
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.font_manager import FontProperties
from matplotlib.path import Path
from matplotlib.textpath import TextToPath

from abses.tools.func import with_axes

if TYPE_CHECKING:
    from abses.actor import Actor
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

    def __init__(self, module: PatchModule):
        self.module = module
        self.model = module.model

    def _retrieve_marker(self, breed, **kwargs) -> Dict[str, str]:
        breed_cls: Type[Actor] = getattr(self.model, "_breeds")[breed]
        marker_kwargs = breed_cls.viz_attrs(**kwargs)
        marker_kwargs["marker"] = get_marker(marker_kwargs["marker"])
        return marker_kwargs

    def _stat_actors(self, breed: str) -> pd.DataFrame:
        matrix = self.module.apply(lambda c: c.agents.has(breed))
        rows, cols = np.where(matrix)
        rows_coords = self.module.coords["y"][rows]
        cols_coords = self.module.coords["x"][cols]
        numbers = matrix[rows, cols]
        return pd.DataFrame(
            {
                "x": cols_coords,
                "y": rows_coords,
                "Number": numbers.flatten(),
                "Breed": breed,
            }
        )

    @with_axes
    def scatter(
        self,
        breeds: Optional[Iterable[str]] = None,
        size: Optional[str] = None,
        hue: Optional[str] = None,
        ax: Optional[Axes] = None,
        # sizes: Tuple[int, int] = (20, 200),
        palette: Optional[str | Dict] = None,
        **kwargs,
    ) -> Axes:
        """Adding"""
        data = []
        if breeds is None:
            breeds = self.model.breeds
        markers_used = {}
        colors = {}
        for breed in breeds:
            data.append(self._stat_actors(breed=breed))
            style_dict = self._retrieve_marker(breed, **kwargs)
            markers_used[breed] = style_dict["marker"]
            colors[breed] = style_dict["color"]
        df = pd.concat(data, axis=0)
        if palette is None and hue == "Breed":
            palette = colors
        sns.scatterplot(
            df,
            x="x",
            y="y",
            ax=ax,
            size=size,
            style="Breed",
            hue=hue,
            markers=markers_used,
            # sizes=sizes,
            palette=palette,
        )
        return ax

    @with_axes
    def show(
        self,
        attr: Optional[str] = None,
        ax: Optional[Axes] = None,
        with_actors: bool = True,
        scatter_kwargs: Optional[Dict[str, Any]] = None,
        legend_kwargs: Optional[Dict[str, Any]] = None,
    ) -> Axes:
        """Show the nature module"""
        if scatter_kwargs is None:
            scatter_kwargs = {}
        if legend_kwargs is None:
            legend_kwargs = {}
        # because of `with_axes`, it must be a valid Axes object
        ax = cast(Axes, ax)
        if attr is None:
            xda = self.module.xda
            xda.plot(ax=ax, add_colorbar=False, alpha=0.8)
        else:
            xda = self.module.get_xarray(attr)
            xda.plot(ax=ax, cbar_kwargs=COLOR_BAR, alpha=0.8)
        if self.model.breeds and with_actors:
            self.scatter(ax=ax, **scatter_kwargs)
        ax.axes.set_aspect("equal")
        if self.model.breeds:
            ax.legend(**legend_kwargs)
        return ax
