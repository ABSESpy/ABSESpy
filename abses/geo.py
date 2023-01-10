#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from numbers import Number
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd
from pyproj.crs.crs import CRS

NODATA = -9999.0
WGS84 = "EPSG:4326"


class Geo:
    def __init__(self, crs=None, dims=None, nodata=None):
        self._crs: CRS = CRS.from_user_input(WGS84)
        self._nodata: float = NODATA
        self._dims: Tuple[str, str] = ("x", "y")

    @property
    def crs(self):
        return self._crs

    @crs.setter
    def crs(self, crs: Union[str, CRS, None]):
        if crs is not None:
            crs = CRS.from_user_input(crs)
        self._crs = crs

    @property
    def nodata(self):
        return self._nodata

    @nodata.setter
    def nodata(self, value):
        self._nodata = value

    @property
    def dims(self) -> Tuple[str, str]:
        return self._dims

    @dims.setter
    def dims(self, dims: Tuple[str, str]):
        self._dims = dims

    @property
    def geographic_crs_name(self) -> str:
        if self.crs is None:
            return "Not exists"
        else:
            return self.crs.name

    @property
    def georef(self):
        georef = {
            "crs": f"{self.geographic_crs_name}",
            "dims": f"{self.dims}",
            "nodata": f"{self.nodata}",
        }
        return georef

    def show_georef(self):
        return pd.Series(self.georef)
