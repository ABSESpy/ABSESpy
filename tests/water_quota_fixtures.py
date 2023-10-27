#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import geopandas as gpd
import xarray as xr
from hydra import compose, initialize

from abses.actor import Actor
from abses.nature import BaseNature, PatchCell, PatchModule

# 加载项目层面的配置
with initialize(version_base=None, config_path="../config"):
    cfg = compose(config_name="water_quota")

CITIES = gpd.read_file(cfg.db.cities)
DATA_ET0 = xr.open_dataarray(cfg.db.et0, decode_coords="all")
DATA_PREC = xr.open_dataarray(cfg.db.prec, decode_coords="all")


class HydroCell(PatchCell):
    """水文单元格"""

    def __init__(self, pos=None, indices=None):
        super().__init__(pos, indices)
        self.etc = None
        self.k_c = None
        self.prec = None


class Hydrology(PatchModule):
    """水文模块"""

    __netCDF_datasets__ = {"prec": DATA_PREC, "et0": DATA_ET0}

    def _reproject_datasets(self):
        """重新切割数据的大小"""
        standard = self.get_xarray()
        for name, data in self.__netCDF_datasets__.items():
            data = data.rio.write_crs(self.crs)
            new_data = data.rio.reproject_match(standard)
            self.__netCDF_datasets__[name] = new_data

    def _attach_dynamic_data(self):
        """为水文模块创建动态数据"""

        def select_data_now(data, time):
            """选择当前时间的 NetCDF 数据，并转换成数组"""
            return data.sel(time=time.dt, method="nearest").to_numpy()

        for name, data in self.__netCDF_datasets__.items():
            self.add_dynamic_variable(
                name=name, data=data, function=select_data_now
            )

    def initialize(self):
        """初始配置"""
        self._reproject_datasets()
        self._attach_dynamic_data()
        self.calculate_etc()

    def calculate_etc(self):
        """计算作物蒸散发"""
        et0 = self.dynamic_var("et0")
        ks = self.params.Ks
        kc = self.linked_attr(attr="Kc", how="only")
        etc = (et0 * ks * kc).reshape(self.shape3d)
        self.apply_raster(etc, attr_name="etc")


class Nature(BaseNature):
    """自然模块"""

    def __init__(self, model, name="nature"):
        super().__init__(model, name)
        # 城市
        self.cities = None
        # 人口是一个图层
        self.pop: PatchModule = self.create_module(
            how="from_file", raster_file=cfg.db.population
        )
        # 水文是另一个图层，并使用自定义的 Cell 类
        self.hydro: Hydrology = self.create_module(
            Hydrology,
            how="copy_layer",
            layer=self.pop,
            cell_cls=HydroCell,
            name="hydro",
        )

    def initialize(self):
        # 城市是 GeoDataFrame 主体
        self.cities = self.create_agents_from_gdf(CITIES, "City_ID")
        super().initialize()


class Farmer(Actor):
    """农民"""


# class Human(BaseHuman):
#     def __init__(self, model, name="human"):
#         super().__init__(model, name)
#         self.economy = self.create_module(Economy)
