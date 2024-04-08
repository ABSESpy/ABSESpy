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
import numpy as np
import pandas as pd
import pytest
import xarray as xr
from pandas.testing import assert_series_equal

from abses import MainModel
from abses.nature import PatchModule
from abses.objects import _BaseObj
from abses.time import TimeDriver


class TestDynamicData:
    """测试动态数据的读取"""

    @pytest.fixture(name="lands_data")
    def setup_lands_data(self, water_quota_config):
        """土地数据"""
        return pd.read_csv(water_quota_config.db.irr_data, index_col=0)

    @pytest.fixture(name="et0_data")
    def setup_et0_data(self, water_quota_config):
        """et0 数据"""
        return xr.open_dataarray(
            water_quota_config.db.et0, decode_coords="all"
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
    def update_et0_function(
        data,
        time,
        obj: PatchModule,
    ) -> np.ndarray:
        """从数据中读取更新的 et0"""
        time = time.dt
        xda = data.sel(time=time, method="nearest").rio.write_crs(obj.crs)
        standard = obj.get_xarray()
        return xda.rio.reproject_match(standard).to_numpy()

    @pytest.fixture(name="model")
    def setup_model(self, water_quota_config, lands_data) -> MainModel:
        """创造可供测试的黄河灌溉用水例子"""
        model = MainModel(seed=42, parameters=water_quota_config)
        gdf = gpd.read_file(water_quota_config.db.cities)
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

    def test_dynamic_nc_data(
        self, model: MainModel, water_quota_config, et0_data
    ):
        """测试黄河灌溉用水主体可以自动从数据中读取 et0"""
        module = model.nature.create_module(
            how="from_file",
            raster_file=water_quota_config.db.population,
        )
        module.add_dynamic_variable(
            name="et0", data=et0_data, function=self.update_et0_function
        )
        model_now = module.dynamic_var("et0")
        assert model_now.shape == module.shape2d

        # 直接从数据中读取
        data_now = et0_data.sel(time=model.time.dt, method="nearest")
        data_now_crs = data_now.rio.write_crs(module.crs)
        matched = data_now_crs.rio.reproject_match(module.get_xarray())

        assert matched.shape == module.shape2d

        # 注意两边的空值 np.nan 在对比时，是不认为相等的，需要填充空值后对比，发现数据就一样了
        assert (
            np.nan_to_num(model_now, 0.0)
            == np.nan_to_num(matched.to_numpy(), 0.0)
        ).all()
