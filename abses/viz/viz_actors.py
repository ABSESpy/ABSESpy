#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""Visualize ActorsList
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Iterable, Literal, Optional

import geopandas as gpd
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib.axes import Axes

from abses.tools.func import with_axes

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

if TYPE_CHECKING:
    from abses.actor import Actor, GeoType
    from abses.main import MainModel
    from abses.sequences import ActorsList

StyleDict: TypeAlias = Dict[str, Dict[str, Any]]


class _VizNodeList:
    def __init__(self, model: MainModel, actors: ActorsList) -> None:
        self.actors = actors
        self.model = model

    def _subset(
        self, geo_type: Optional[GeoType | bool] = None
    ) -> ActorsList[Actor]:
        """Returns dataset for plotting."""
        if geo_type is None:
            return self.actors
        if isinstance(geo_type, bool):
            selection: Dict[str, Any] = {"on_earth": geo_type}
        elif geo_type in ("Point", "Shape"):
            selection = {"geo_type": geo_type}
        return self.actors.select(selection)

    @with_axes(figsize=(6, 4))
    def hist(
        self,
        attr: str,
        ax: Optional[Axes] = None,
        savefig: Optional[str | Path] = None,
        palette: Optional[str | Dict] = None,
    ):
        """Plot hist."""
        df = self._subset().summary(attrs=attr)
        if palette is None:
            palette = self._style_dict("color", "blue")
        sns.histplot(df, x=attr, ax=ax, hue="breed", palette=palette)
        if savefig:
            plt.savefig(savefig)
            plt.close()
        return ax

    def _style_dict(self, request: str, default: Any, **kwargs) -> StyleDict:
        styles = {}
        for breed in self.actors.to_dict().keys():
            breed_cls = self.model.breeds[breed]
            style_dict = breed_cls.viz_attrs(render_marker=True, **kwargs)
            styles[breed] = style_dict.get(request, default)
        return styles

    @with_axes
    def show(
        self,
        boundary: bool = False,
        ax: Optional[Axes] = None,
    ) -> Axes:
        """Show the shapefile."""
        subset = self._subset(geo_type="Shape")
        data = gpd.GeoSeries(
            subset.array("geometry"), crs=self.model.nature.crs
        )
        obj = data.boundary if boundary else data
        obj.plot(ax=ax)
        return ax

    @with_axes
    def positions(
        self,
        coords: bool = True,
        ax: Optional[Axes] = None,
        hue: Optional[str] = "breed",
        size: Optional[str] = None,
        palette: Optional[str | Dict] = None,
        **kwargs,
    ) -> Axes:
        """Plotting spatial distribution of the actors."""
        data = self._subset(geo_type="Point").summary(coords=coords)
        y_axis = "y" if coords else "row"
        x_axis = "x" if coords else "col"
        count_data = (
            data.groupby([y_axis, x_axis, "breed"])
            .size()
            .reset_index(name="count")
        )
        if hue == "breed":
            palette = self._style_dict("color", "blue")
        sns.scatterplot(
            x=x_axis,
            y=y_axis,
            size=size,
            data=count_data,
            hue=hue,
            ax=ax,
            style="breed",
            markers=self._style_dict("marker", "o"),
            palette=palette,
            **kwargs,
        )
        return ax
