#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/
import copy
from collections.abc import Iterable
from functools import cached_property
from typing import Optional

import numpy as np
import rioxarray
import xarray as xr
from scipy import ndimage

from .bases import Creation
from .geo import Geo

# from src.abm_chans.visualization import PatchViz


# TODO use a decorator function instead of recalc


def update_array(
    array,
    value: "np.ndarray|str|bool|float",
    mask: np.ndarray = None,
):
    """
    Update a groundwater 2-d array's attributions.

    Arguments:
        value -- Change to the new value. Can be a new array (shape is same as the masked matrix' shape.) or a single value.
        mask -- Which element to change, default {None}, then all elements will be set.

    Returns:
        Changed mask, where have been changed.
    """
    if mask is None:
        mask = np.ones(array.shape, dtype=bool)
    if isinstance(value, Iterable):
        if value.shape == array.shape:
            array[mask] = value[mask]
        elif len(value) == mask.sum():
            array[mask] = value
        else:
            raise TypeError(f"Not support {type(value)}")
    else:
        array[mask] = value
    return array


class ArrayOperation:
    def __init__(self, array):
        self.array = array

    def buffer(self, buffer=1, neighbors=4):
        if neighbors == 4:
            connectivity = 1
        elif neighbors == 8:
            connectivity = 2
        struct = ndimage.generate_binary_structure(2, connectivity)
        result = self.array.copy()
        i = 1
        while i <= buffer:
            result = ndimage.binary_dilation(result, structure=struct).astype(
                self.array.dtype
            )
            i += 1
        return result

    def unique(self) -> np.ndarray:
        return np.unique(self.array)

    def sort(self, *args, **kwargs) -> np.ndarray:
        axis = kwargs.pop("axis", None)
        return np.sort(self.array, axis=axis, *args, **kwargs)

    def where(self):
        return list(zip(*np.where(self.array)))


class GeoXarray:
    def __init__(self, xda: xr.DataArray, geo: Geo):
        self._obj: xr.DataArray = self.setup_spatial(xda, geo)
        self._geo: Geo = geo

    def setup_spatial(self, xda, geo: Geo) -> xr.DataArray:
        xda = xda.rio.write_crs(geo.crs)
        xda = xda.rio.set_spatial_dims(x_dim=geo.dims[0], y_dim=geo.dims[0])
        xda = xda.rio.set_nodata(geo.nodata)
        xda = xda.rio.write_coordinate_system()
        return xda

    @property
    def resolution(self):
        affine = self._obj.rio.transform()
        size_x = abs(affine[0])
        size_y = abs(affine[4])
        return size_x, size_y

    @cached_property
    def area(self):
        x, y = self.resolution
        area = x * y
        self._area = area
        return area

    def resampling(self, factor):
        from rasterio.enums import Resampling

        xds = self._obj.transpose("lat", "lon")
        new_width = xds.rio.width * factor
        new_height = xds.rio.height * factor
        scaled = xds.rio.reproject(
            xds.rio.crs,
            shape=(new_height, new_width),
            resampling=Resampling.bilinear,
        )
        return scaled


class Patch(np.ndarray, Creation):
    def __new__(
        cls,
        array: np.ndarray,
        name: Optional[str] = None,
        father: Optional[object] = None,
        xarray: Optional[bool] = False,
    ):
        obj = np.asarray(array).view(cls)
        obj._farther = father
        obj._name = name
        obj._check_valid()
        obj._xda: xr.DataArray = None
        obj._rio: GeoXarray = None
        if xarray:
            obj.to_xarray(recalc=True)
        return obj

    @property
    def arr(self) -> ArrayOperation:
        return ArrayOperation(self.view(np.ndarray))

    # @property
    # def plot(self) -> PatchViz:
    #     xarray = self.xda
    #     return PatchViz(xarray)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def father(self):
        return self._farther

    @property
    def xda(self) -> xr.DataArray:
        return self._xda

    @property
    def rio(self) -> GeoXarray:
        if self._rio is None:
            return self.to_spatial(True)
        else:
            return self._rio

    @property
    def cell_area(self):
        # TODO: refactor this into global variable
        return self.rio.area()

    def _check_valid(self) -> bool:
        if len(self.shape) != 2:
            raise ValueError("Invalid shape.")
        return True

    def __array_finalize__(self, obj):
        if obj is None:
            return
        self.name = getattr(obj, "name", None)

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        # this method is called whenever you use a ufunc
        # i.e., symbols like +, -, *, / ...
        # https://stackoverflow.com/questions/51520630/subclassing-numpy-array-propagate-attributes
        f = {
            "reduce": ufunc.reduce,
            "accumulate": ufunc.accumulate,
            "reduceat": ufunc.reduceat,
            "outer": ufunc.outer,
            "at": ufunc.at,
            "__call__": ufunc,
        }
        output = f[method](
            *(
                i.view(np.ndarray) if isinstance(i, Patch) else i
                for i in inputs
            ),
            **kwargs,
        )
        # output.__dict__ = self.__dict__  # carry forward attributes
        return output

    def update(
        self,
        value: "np.ndarray|str|bool|float",
        mask: np.ndarray = None,
    ):
        """
            Update a groundwater 2-d array's attributions.

            Arguments:
                value -- Change to the new value. Can be a new array (shape is same as the masked matrix' shape.) or a single value.
                mask -- Which element to change, default {None}, then all elements will be set.

        Returns:
            Changed mask, where have been changed.
        """
        update_array(self, value, mask)
        if self.xda is not None:
            update_array(self.xda.data, value, mask)

    def to_xarray(self, recalc: bool = True) -> xr.DataArray:
        if recalc is False:
            return self._xda
        if self.father is None:
            raise ValueError("father of patch must be specified")
        xda = xr.DataArray(
            data=self,
            name=self.name,
            coords=self.father.coords,
            attrs=self.father.attrs,
        ).where(self.father.accessible)
        self._xda = xda
        return xda

    def to_spatial(self, recalc: bool = False) -> None:
        if self.xda is None:
            # raise AB_EGMpyError("patch", wrong="convert", condition="")
            raise ValueError("to_spatial requires patch")
        if recalc is True:
            self._rio = GeoXarray(self.xda, self.father)
        return self.rio
