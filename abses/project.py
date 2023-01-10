#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import logging
import os

import dill as pickle

logger = logging.getLogger(__name__)


class Folder:
    def __init__(self, base):
        base = self.base_is_valid(base)
        self._base = base

    @property
    def path(self):
        return os.path.join(os.getcwd(), self.base)

    @property
    def base(self):
        return self._base

    def base_is_valid(self, base, create: bool = False):
        if base is None:
            base = ""
            logger.warning(
                f"Setup with NO location specified, will save under: {os.getcwd()}"
            )
        if create:
            self.create_path()
        return base

    def create_path(self, folder: str = "") -> str:
        path = os.path.join(self.path, folder)
        if not os.path.exists(path):
            os.mkdir(path)
        return path

    def to_pickle(self):
        file_path = os.path.join(self.path, f"{self.name}.pkl")
        with open(file_path, "wb") as pkl:
            pickle.dump(obj=self, file=pkl)
        logger.info(f"Model {self.name} saved under {self.path}.")

    pass
