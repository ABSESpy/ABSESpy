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


class PatchFactory(Creator):
    _valid_type = (bool, int, float, str, "float32")
    _valid_dtype = tuple([np.dtype(t) for t in _valid_type])

    def __init__(self, model, shape=None, **kwargs):
        Creator.__init__(self)
        self._geo = Geo(model)
        self._mask = None
        # Other attrs
        self._attrs = kwargs.copy()

    @property
    def geo(self):
        return self._geo

    @property
    def shape(self):
        return self.geo.shape

    @shape.setter
    def shape(self, value: Tuple[int, int]):
        if value == self.shape:
            pass
        else:
            msg = f"Geographic shape {self.shape}, NOT allow to change it!"
            raise ValueError(msg)

    @property
    def mask(self) -> xarray.DataArray:
        return self.geo.wrap_data(self._mask, mask=True)

    @property
    def accessible(self):
        if self.mask is None:
            return None
        else:
            return ~self.mask

    @property
    def attrs(self):
        return self._attrs

    def _check_dtype(self, values) -> None:
        dtype = values.dtype
        if dtype not in self._valid_dtype:
            raise TypeError(f"Invalid value type {dtype}.")

    def _check_type(self, value) -> type:
        val_type = type(value)
        if val_type not in self._valid_type:
            raise ValueError(f"Invalid type {val_type}")

    def _check_shape(self, values):
        if values.shape != self.geo.shape:
            raise ValueError(
                f"Invalid shape {values.shape}, mismatch with shape {self.shape}."
            )

    def _check_name(self, name):
        pass

    def full_array(self, value):
        if not self.shape:
            raise ValueError("Shape is not assigned.")
        else:
            return np.full(self.shape, value)

    def create_patch(
        self,
        values: "np.ndarray|str|bool|float|int",
        name: str,
        xarray: bool = True,
    ) -> Patch:
        if not hasattr(values, "shape"):
            # only int|float|str|bool are supported
            self._check_type(values)
            values = self.full_array(values)
        else:
            # nd-array like data
            self._check_dtype(values)
            self._check_shape(values)
        self._check_name(name)
        patch = Patch(values, name=name, father=self, xarray=xarray)
        self.add_creation(patch)
        return patch

    def generate_boundary(self, settings: Optional[dict] = None) -> Boundaries:
        # resolution = settings.pop("resolution", 1)
        boundary = simple_boundary_from(settings)
        self.shape = boundary.shape
        # self.coords = self.setup_coords(width, height, resolution)
        self.mask = ~boundary.interior
        self.boundary = boundary
        self.notify()
        return boundary
