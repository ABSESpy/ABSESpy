#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import netCDF4
import rasterio
import rioxarray
import xarray as xr

from abses import Actor, MainModel


def test_clip():
    # as same as read this from `.yaml` file.
    parameters = {"nature": {"world": r"data/clipped.tif"}}
    model = MainModel(name="geo testing", base="tests", parameters=parameters)
    xda = rasterio.open(r"data/clipped.tif", band=1)
    # model.nature.accessible.plot()
    assert xda.shape == model.nature.geo.shape
    path = "data/prec_CMFD_V0106_B-01_01mo_010deg_197901-201812.nc"
    # xda = xr.open_dataset(path, decode_coords='all')
    patch = model.nature.read_patch(path, name="prec")
    assert patch.shape == xda.shape
