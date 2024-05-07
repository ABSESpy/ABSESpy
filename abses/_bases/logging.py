#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import sys

from loguru import logger

logger.add(
    sys.stderr,
    format="{time} {level} {message}",
    level="WARNING",
    colorize=True,
)
