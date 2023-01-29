#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import pathlib
from typing import Callable, Union

import netCDF4
import numpy as np
import rioxarray
import xarray

from abses.geo import Geo
from abses.time import TimeDriver


class GeoEngine:
    def __new__(cls, path, model):
        instance = super().__new__(cls)
        instance.path = pathlib.Path(path)
        instance.model = model
        instance.geo = model.nature.geo
        instance.time = model.time
        return instance

    # def __init__(self, path, geo, time):
    #     super().__init__(self, path)
    #     self.geo = geo
    #     self.time = time

    def read2array(
        self,
        resample_method: Union[str, Callable] = "mean",
        selecting_method: str = "nearest",
    ) -> np.ndarray:
        if self.path.suffix in [".tif", ".tiff"]:
            pass
        elif self.path.suffix in [".nc"]:
            xda = xarray.open_dataarray(
                self.path.absolute(), decode_coords="all"
            )
            resampled = xda.resample(time=self.time.freq).mean()
            xda_now = resampled.sel(
                time=self.time.period.to_timestamp("S"),
                method=selecting_method,
            )
            matched_xda = self.geo.clip_match(xda_now)
            return matched_xda.to_numpy()

    pass
