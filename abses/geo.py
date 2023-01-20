#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

import threading
from numbers import Number
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
    TypeAlias,
    Union,
)

import numpy as np
import pandas as pd
from pyproj.crs.crs import CRS

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

    @property
    def shape(self) -> Tuple[int, int]:
        return self.height, self.width

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
    def georef(self):
        georef = {
            "crs": f"{self.geographic_crs_name}",
            "dims": f"{self.dims}",
            "nodata": f"{self.nodata}",
        }
        return georef

    @property
    def width(self):
        return len(self._x)

    @property
    def height(self):
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
            self.dims[0]: self.x,
            self.dims[1]: self.y,
        }
        return coords

    def show_georef(self):
        return pd.Series(self.georef)

    def retrieve_georef(self, **kwargs) -> None:
        self.crs = kwargs.pop("crs", None)
        self._nodata = kwargs.pop("nodata", NODATA)

    def setup_from_coords(
        self,
        coord_x: Coordinate,
        coord_y: Coordinate,
        **kwargs: Dict[str, Any],
    ) -> Shape2:
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
        return self.shape

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
        return self.shape
