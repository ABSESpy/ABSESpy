#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import logging
import logging.config
import os

import yaml

from .tools.func import iter_func

CONFIG_PATH = os.path.join(os.getcwd(), "config/log.yaml")
with open(CONFIG_PATH, "rt") as f:
    config_data = yaml.safe_load(f.read())
    logging.config.dictConfig(config_data)


class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """

    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ""

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())


def clean_logs():
    handlers = config_data.get("handlers")
    removed_handlers = []
    for handler, configs in handlers.items():
        filename = configs.get("filename")
        if not filename:
            continue
        file_path = os.path.join(os.getcwd(), filename)
        open(file_path, "w").close()
        removed_handlers.append(handler)
    logging.warning(f"Logs of {removed_handlers} cleared.")


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
