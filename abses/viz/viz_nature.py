#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""Viz natural module.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, cast

from matplotlib.axes import Axes

from abses.tools.func import with_axes
from abses.tools.viz import COLOR_BAR

if TYPE_CHECKING:
    from abses.actor import Actor
    from abses.nature import PatchModule


class _VizNature:
    """Visualize the nature module"""

    def __init__(self, module: PatchModule):
        self.module = module
        self.model = module.model

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
            self.model.actors.plot.positions(ax=ax, **scatter_kwargs)
        ax.axes.set_aspect("equal")
        if self.model.breeds:
            ax.legend(**legend_kwargs)
        return ax
