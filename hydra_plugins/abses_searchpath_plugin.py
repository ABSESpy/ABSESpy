#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""This is for SearchPathPlugin of hydra
"""

from hydra.core.config_search_path import ConfigSearchPath
from hydra.plugins.search_path_plugin import SearchPathPlugin


class ABSESpySearchPathPlugin(SearchPathPlugin):
    """Plugin to add additional search paths to hydra's default searchpaths."""

    def manipulate_search_path(self, search_path: ConfigSearchPath) -> None:
        """
        Add additional search paths for configurations for hydra.

        Args:
            search_path: Search path used by hydra

        Returns:
            None
        """
        search_path.append(provider="abses", path="pkg://abses/conf")
