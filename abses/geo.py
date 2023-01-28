#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

import os
import threading
from functools import cached_property
from numbers import Number
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Self,
    Sequence,
    Tuple,
    Type,
    TypeAlias,
    Union,
)

import numpy as np
import pandas as pd
import rioxarray
import xarray as xr
from pyproj.crs.crs import CRS

from .tools.read_files import read_yaml

if TYPE_CHECKING:
    from abses.main import MainModel


NODATA = -9999.0
WGS84 = "EPSG:4326"

Coordinate: TypeAlias = Union[Iterable[Number], Dict[str, Iterable[Number]]]
Shape2: TypeAlias = Tuple[int, int]


class Geo:
    """Singleton AgentsContainer for each model."""

    _models: Dict[MainModel, Geo] = {}
    _lock = threading.RLock()

    def __new__(cls: type[Self], model: MainModel) -> Self:
        instance = cls._models.get(model, None)
        if instance is None:
            instance = super().__new__(cls)
            with cls._lock:
                cls._models[model] = instance
        return instance

    def __init__(self, model=None):
        self._model = model
        self._crs: CRS = None
        self._nodata: float = None
        self._dims: Tuple[str, str] = ("x", "y")
        self._x: Optional[np.ndarray] = None
        self._y: Optional[np.ndarray] = None
        self._mask: Optional[np.ndarray] = None

    @property
    def shape(self) -> Tuple[int, int]:
        return self.height, self.width

    @property
    def mask(self) -> xr.DataArray:
        if self._mask is None:
            return self.zeros()
        else:
            return self.wrap_data(self._mask)

    @property
    def accessible(self) -> xr.DataArray:
        return ~self.mask

    @property
    def crs(self) -> CRS:
        return self._crs

    @crs.setter
    def crs(self, crs: Union[str, CRS, None]):
        if crs is not None:
            crs = CRS.from_user_input(crs)
        self._crs = crs

    @property
    def nodata(self) -> float:
        return self._nodata

    @nodata.setter
    def nodata(self, value: float):
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
    def georef(self) -> Dict[str, Any]:
        georef = {
            "crs": f"{self.geographic_crs_name}",
            "dims": f"{self.dims}",
            "nodata": f"{self.nodata}",
        }
        return georef

    @property
    def width(self) -> int:
        return len(self._x)

    @property
    def height(self) -> int:
        return len(self._y)

    @property
    def x(self) -> np.ndarray:
        return self._x

    @property
    def y(self) -> np.ndarray:
        return self._y

    @property
    def coords(self) -> Dict[str, np.ndarray]:
        coords = {
            self.dims[1]: self.y,
            self.dims[0]: self.x,
        }
        return coords

    def _setup_mask(self, value):
        if not hasattr(value, "shape"):
            raise AttributeError("Mask must has 'shape' attribute")
        elif value.shape != self.shape:
            raise ValueError(
                f"Input shape {value.shape} does not match {self.shape}."
            )
        self._mask = value

    def show_georef(self) -> pd.Series:
        return pd.Series(self.georef)

    def retrieve_georef(self, **kwargs) -> None:
        self.crs = kwargs.pop("crs", WGS84)
        self._nodata = kwargs.pop("nodata", NODATA)

    def setup_from_coords(
        self,
        coord_x: Coordinate,
        coord_y: Coordinate,
        **kwargs: Dict[str, Any],
    ) -> None:
        """
        Setup geographic references from coordinates.

        Args:
            coords (Tuple[int, int]): a dictionary of coordinates. Must be 2-dimensions coords. The following notations are accepted:
                    - mapping {dimension name: array-like}
                    - sequence of tuples that are valid arguments for
                    ``xarray.Variable()``
                    - (dims, data)
                    - (dims, data, attrs)
                    - (dims, data, attrs, encoding)
                If a list, it should be a list of tuples where the first element is the dimension name and the second element is the corresponding coordinate array_like object. see documentation of `Xarray` https://docs.xarray.dev/en/stable/user-guide/data-structures.html.

        Returns:
            Tuple[int, int]: shape of the array.
        """

        def parse_coord(coord, default):
            if isinstance(coord, dict):
                name = coord.get("name", default)
                data = coord["data"]
            else:
                name = default
                data = np.array(coord)
                if len(data.shape) != 1:
                    raise TypeError
            return name, data

        x, self._x = parse_coord(coord_x, "x")
        y, self._y = parse_coord(coord_y, "y")
        self._dims = (x, y)
        self.retrieve_georef(**kwargs)

    def setup_from_shape(
        self,
        shape: Tuple[int, int],
        resolution: Union[int, float] = 1,
        **kwargs,
    ) -> None:
        height, width = shape
        self._x = np.arange(0, width * resolution, resolution)
        self._y = np.arange(0, height * resolution, resolution)
        self.retrieve_georef(**kwargs)

    @staticmethod
    def detect_dims(dims: Tuple[str]) -> Tuple[str]:
        if "x" in dims and "y" in dims:
            return ("x", "y")
        elif "lon" in dims and "lat" in dims:
            return ("lon", "lat")
        elif "longitude" in dims and "latitude" in dims:
            return ("longitude", "latitude")
        else:
            raise ValueError("Unknown dimensions %s." % dims)

    def setup_from_dict(self, settings: dict) -> None:
        shape = settings.pop("shape", None)
        resolution = settings.pop("resolution", 1)
        if shape is None:
            try:
                width = settings.pop("width")
                height = settings.pop("height")
            except KeyError:
                raise KeyError(
                    f"'shape' or ('width' and 'height') not specified in {settings.keys()}!"
                )
            shape = (height, width)
        self.setup_from_shape(shape=shape, resolution=resolution, **settings)

    def setup_from_file(self, filename: str) -> None:
        path = Path(filename)
        if not path.is_file():
            raise ValueError("Could not find file %s" % filename)
        if path.suffix in [".tiff", ".tif"]:
            xda = rioxarray.open_rasterio(filename)
            dims = self.detect_dims(xda.dims)
            x_coord = xda.coords[dims[0]].to_dict()
            y_coord = xda.coords[dims[1]].to_dict()
            self.setup_from_coords(x_coord, y_coord, **xda.attrs)
            nodata = xda.isnull().data.reshape(self.shape)
            self._setup_mask(nodata)
        elif path.suffix in [".yaml"]:
            settings = read_yaml(path)
            self.setup_from_dict(settings)
        else:
            raise ValueError(f"Unknown referring file type {path.suffix}.")

    def auto_setup(self, settings: Union[str, dict]) -> None:
        if isinstance(settings, str):
            self.setup_from_file(settings)
        elif isinstance(settings, dict):
            self.setup_from_dict(settings)
        else:
            raise TypeError(f"Not support '{type(settings)}'.")

    def zeros(self, dtype: Type = bool) -> xr.DataArray:
        data = np.zeros(self.shape, dtype=dtype)
        return self.wrap_data(data, masked=False)

    def ones(self, dtype: Type = bool) -> xr.DataArray:
        data = np.ones(self.shape, dtype=dtype)
        return self.wrap_data(data, masked=False)

    def wrap_data(
        self, data: Optional[np.ndarray] = None, masked: bool = False
    ) -> xr.DataArray:
        if data is None:
            return self.accessible
        xda = xr.DataArray(data, coords=self.coords)
        xda.rio.write_crs(self.crs, inplace=True)
        if masked is True:
            return xda.where(self.accessible)
        else:
            return xda

    def clip_match(self, xda: xr.DataArray) -> xr.DataArray:
        xda = xda.rio.write_crs(self.crs)
        aligned = xda.rio.reproject_match(self.accessible)
        return aligned
