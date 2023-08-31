#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from abses.time import TimeDriver

from .bases import Observer
from .log import Log

if TYPE_CHECKING:
    from abses.main import MainModel


class BaseObj(Observer, Log):
    """
    基础对象，所有可以被用户自定义的对象都应该继承此类，包括：
    自然模块，人类模块，子模块，主体。
    其特点是这些模块可以访问模型的全局变量、时间驱动器，以及有各种自定义变量。
    """

    def __init__(
        self,
        model: MainModel,
        observer: Optional[bool] = True,
        name: Optional[str] = None,
    ):
        Log.__init__(self, name=name)
        self.time = TimeDriver(model)
        if observer:
            model.attach(self)
