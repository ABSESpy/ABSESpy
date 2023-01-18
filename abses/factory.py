#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from typing import Dict, Optional, Sequence, Tuple

import numpy as np

from .bases import Creator
from .boundary import Boundaries, simple_boundary_from
from .geo import Geo
from .patch import Patch


class PatchFactory(Creator, Geo):
    _valid_type = (bool, int, float, str, "float32")
    _valid_dtype = tuple([np.dtype(t) for t in _valid_type])

    def __init__(self, shape=None, mask=None, **kwargs):
        Creator.__init__(self)
        Geo.__init__(self)
        self.shape = shape
        self.mask = mask
        self._x: Optional[np.ndarray] = None
        self._y: Optional[np.ndarray] = None
        self._coords: Optional[Dict] = None  # todo refactor this
        # Patch inheritances
        self.inheritance = ["shape"]
        # Other attrs
        self._attrs = kwargs.copy()
        self._boundary = None

    @property
    def width(self):
        return self.shape[1]

    @property
    def height(self):
        return self.shape[0]

    @property
    def x(self) -> np.ndarray:
        if self._x is None:
            return np.arange(self.width)
        else:
            return self._x

    @property
    def y(self) -> np.ndarray:
        if self._y is None:
            return np.arange(self.height)
        else:
            return self._y

    @property
    def coords(self) -> Dict[str, np.ndarray]:
        if self._coords is not None:
            return self._coords
        coords = {
            self.dims[1]: self.y,
            self.dims[0]: self.x,
        }
        return coords

    @coords.setter
    def coords(self, coords: Tuple[np.ndarray, np.ndarray]):
        self._x = coords[0]
        self._y = coords[1]

    @property
    def mask(self) -> np.ndarray:
        return self._mask

    @mask.setter
    def mask(self, mask: np.ndarray = None) -> None:
        if mask is None and self.shape:
            mask = np.zeros(self.shape, bool)
        elif mask is None and self.shape is None:
            mask = None
        self._mask = mask

    @property
    def accessible(self):
        if self.mask is None:
            return None
        else:
            return ~self.mask

    @property
    def attrs(self):
        return self._attrs

    @property
    def boundary(self):
        return self._boundary

    @boundary.setter
    def boundary(self, boundary):
        self._check_boundary(boundary)
        self._boundary = boundary

    def _check_boundary(self, boundary):
        if not isinstance(boundary, Boundaries):
            raise TypeError("boundary must be Boundaries")

    def _check_dtype(self, values) -> None:
        dtype = values.dtype
        if dtype not in self._valid_dtype:
            raise TypeError(f"Invalid value type {dtype}.")

    def _check_type(self, value) -> type:
        val_type = type(value)
        if val_type not in self._valid_type:
            raise ValueError(f"Invalid type {val_type}")

    def _check_shape(self, values):
        if not hasattr(values, "shape"):
            raise ValueError(f"Invalid type {type(values)}.")
        if values.shape != self.shape:
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

    def setup_coords(
        self, resolution: "int|float"
    ) -> Tuple[np.ndarray, np.ndarray]:
        width = height = resolution
        x_arr = np.arange(0, width * self.width, width)
        y_arr = np.arange(0, height * self.height, height)
        return x_arr, y_arr

    def generate_boundary(self, settings: Optional[dict] = None) -> Boundaries:
        resolution = settings.pop("resolution", 1)
        boundary = simple_boundary_from(settings)
        self.shape = boundary.shape
        self.coords = self.setup_coords(resolution)
        self.mask = ~boundary.interior
        self.boundary = boundary
        self.notify()
        return boundary
