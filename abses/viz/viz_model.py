#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""Visualize model's dynamic.
"""
from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any, Iterable, List, Optional

from matplotlib.axes import Axes

from abses.tools.func import with_axes

if TYPE_CHECKING:
    from abses import MainModel


class _VizModel:
    def __init__(self, model: MainModel[Any, Any]):
        self.model = model
        self.data = model.datacollector.get_model_vars_dataframe()

    @functools.cached_property
    def variables(self) -> List[str]:
        """Variables that the model recorded in each tick."""
        return list(self.model.datacollector.model_reporters.keys())

    @with_axes
    def lineplot(
        self,
        variables: Optional[Iterable[str]] = None,
        ax: Optional[Axes] = None,
    ) -> Axes:
        """Draw the line of variables."""
        if variables is None:
            variables = self.variables
        return self.data[variables].plot(ax=ax)
