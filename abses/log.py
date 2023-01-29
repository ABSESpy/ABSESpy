#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import logging
import logging.config

from .tools.func import iter_func


# TODO change a specific log for experiments
class Log(object):
    def __init__(self, name):
        if name is None:
            name = self.__class__.__name__.lower()
        self._name = name
        self._log = logging.getLogger(name)
        self._log_flag = True

    @property
    def name(self) -> str:
        return self._name

    @property
    def logger(self):
        return self._log

    @property
    def log_flag(self):
        return self._log_flag

    @iter_func("modules")
    def close_log(self):
        self._log_flag = False
