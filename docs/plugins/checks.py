#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from mkdocs.config import Config

# 这个地方可以加入一些自定义的工作流，在部署文档的时候运行。
# https://github.com/pydantic/pydantic/blob/main/docs/plugins/main.py


def on_pre_build(config: Config) -> None:
    """
    Before the build starts.
    """
