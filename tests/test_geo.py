#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import numpy as np
import xarray as xr

from abses.geo import Geo


def test_setup_from_shape():
    geo = Geo(1)
    geo.setup_from_shape((3, 4), resolution=10)
    assert geo.crs is None
    assert geo.shape == (3, 4)
    assert geo.height == 3
    assert geo.width == 4
    assert geo.nodata == -9999.0
    assert geo.dims == ("x", "y")
    assert (geo.x == np.array([0, 10, 20, 30])).all()
    assert (geo.y == np.array([0, 10, 20])).all()


def test_setup_from_coords():
    geo = Geo(2)
    data = xr.DataArray(
        np.zeros((3, 4)), coords={"y": [1, 2, 3], "x": [2, 4, 6, 8]}
    )
    geo.setup_from_coords(
        data.coords["x"].to_dict(), data.coords["y"].to_dict()
    )
    geo3 = Geo(3)
    geo3.setup_from_coords(coord_y=[1, 2, 3], coord_x=[2, 4, 6, 8])
    assert geo.crs is geo3.crs is None
    assert geo.shape == geo3.shape == (3, 4)
    assert geo.height == geo3.height == 3
    assert geo.width == geo3.width == 4
    assert geo.nodata == -9999.0
    assert geo.dims == geo3.dims == ("x", "y")
    assert (geo.x == np.arange(2, 10, 2)).all()
    assert (geo3.y == np.arange(1, 4)).all()


def test_setup_from_file():
    geo4 = Geo(4)
    geo4.setup_from_file("data/mean_prec.tif")
    assert geo4.shape == (400, 700)
    geo5 = Geo(5)
    geo5.auto_setup("config/world.yaml")
    assert geo5.shape == (9, 9)
    assert (geo5.x == np.arange(0, 90, 10)).all()
