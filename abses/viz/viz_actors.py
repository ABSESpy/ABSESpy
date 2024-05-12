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
from typing import TYPE_CHECKING, Optional

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib.axes import Axes

from abses.tools.func import with_axes

if TYPE_CHECKING:
    from abses.sequences import ActorsList


class _VizNodeList:
    def __init__(self, actors: ActorsList) -> None:
        self.actors = actors

    @with_axes(figsize=(6, 4))
    def hist(
        self,
        attr: str,
        ax: Optional[Axes] = None,
        savefig: Optional[str | Path] = None,
    ):
        """Plot hist."""
        breed = self.actors.array("breed")
        value = self.actors.array(attr=attr)
        df = pd.DataFrame({"breed": breed, attr: value})
        sns.histplot(df, x=attr, ax=ax, hue="breed")
        if savefig:
            plt.savefig(savefig)
            plt.close()
        return ax
