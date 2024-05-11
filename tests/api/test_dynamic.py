#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
Test dynamic data.
"""

import geopandas as gpd
import pandas as pd
import pytest
import xarray as xr
from pandas.testing import assert_series_equal

from abses import MainModel
from abses._bases.objects import _BaseObj
from abses.data import load_data
from abses.time import TimeDriver


class TestDynamicData:
    """测试动态数据的读取"""

    @pytest.fixture(name="lands_data")
    def setup_lands_data(self):
        """土地数据"""
        return pd.read_csv(load_data("irr_lands.csv"), index_col=0)

    @pytest.fixture(name="prec")
    def setup_nc_data(self):
        """et0 数据"""
        return xr.open_dataarray(
            load_data("precipitation.nc"), decode_coords="all"
        )

    @pytest.fixture(name="crops_id")
    def setup_crops_id(self, water_quota_config):
        """作物 id"""
        return list(water_quota_config.crops_id)

    @staticmethod
    def get_lands_data(
        data: pd.DataFrame,
        obj: _BaseObj,
        time: TimeDriver,
    ) -> pd.Series:
        """从数据中读取主体的土地情况"""
        index = data["Year"] == time.year
        data_tmp = data.loc[index].set_index("City_ID")
        return data_tmp.loc[f"C{obj.unique_id}"]

    @staticmethod
    def update_prec_function(
        data,
        time,
    ) -> xr.DataArray:
        """Update precipitation dataset."""
        return data.sel(time=time.dt, method="nearest")

    @pytest.fixture(name="model")
    def setup_model(self, water_quota_config, lands_data) -> MainModel:
        """创造可供测试的黄河灌溉用水例子"""
        model = MainModel(seed=42, parameters=water_quota_config)
        gdf = gpd.read_file(load_data("YR_cities.zip"))
        agents = model.agents.new_from_gdf(gdf=gdf, unique_id="City_ID")
        agents.trigger(
            func_name="add_dynamic_variable",
            name="lands",
            data=lands_data,
            function=self.get_lands_data,
        )
        return model

    def test_dynamic_city_lands(self, model: MainModel, lands_data):
        """测试黄河灌溉用水主体可以自动从数据中读取土地情况"""

        def get_test_data(agent, year):
            data_now = lands_data[lands_data["Year"] == year].set_index(
                "City_ID"
            )
            return data_now.loc[f"C{agent.unique_id}"]

        # 随机选择一个主体
        agent = model.agents.get().random.choice()
        data_1979 = get_test_data(agent, 1979)
        assert_series_equal(agent.dynamic_var("lands"), data_1979)

        # 时间前进一步，到1980年1月，应该更新数据
        model.time.go()
        data_1980 = get_test_data(agent, 1980)
        assert_series_equal(agent.dynamic_var("lands"), data_1980)

        # 再前进一步，到1980年2月，数据不用更新
        model.time.go()
        assert_series_equal(agent.dynamic_var("lands"), data_1980)

    def test_dynamic_nc_data(self, model: MainModel, prec):
        """Testing load NC data and reproject it dynamically."""
        module = model.nature.create_module(
            how="from_file",
            raster_file=load_data("farmland.tif"),
            apply_raster=True,
        )
        module.add_dynamic_variable(
            name="prec",
            data=prec,
            function=self.update_prec_function,
            cover_crs=True,
        )
        model_now = module.dynamic_var("prec", dtype="xarray")
        assert model_now.shape == module.shape2d
