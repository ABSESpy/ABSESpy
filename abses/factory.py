#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from functools import cached_property
from typing import Optional, Tuple

import numpy as np
import xarray

from .bases import Creator
from .boundary import Boundaries, simple_boundary_from
from .geo import Geo
from .patch import Patch

# def generate_boundary(self, settings: Optional[dict] = None) -> Boundaries:
#     # resolution = settings.pop("resolution", 1)
#     boundary = simple_boundary_from(settings)
#     self.shape = boundary.shape
#     # self.coords = self.setup_coords(width, height, resolution)
#     self.mask = ~boundary.interior
#     self.boundary = boundary
#     self.notify()
#     return boundary
