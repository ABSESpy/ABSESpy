#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr
from hydra import compose, initialize
from pint import UnitRegistry

from abses.actor import Actor
from abses.nature import BaseNature, PatchCell, PatchModule
from abses.objects import BaseObj
from abses.sequences import ActorsList
from abses.time import TimeDriver
from examples.water_quota.farmer import Farmer

# 加载项目层面的配置
with initialize(version_base=None, config_path="."):
    cfg = compose(config_name="config")

ureg = UnitRegistry()  # 注册单位
ureg.define("TMC = 1e8 m ** 3")

CITIES = gpd.read_file(cfg.db.cities)
DATA_ET0 = xr.open_dataarray(cfg.db.et0, decode_coords="all")
DATA_PREC = xr.open_dataarray(cfg.db.prec, decode_coords="all")
LANDS_DATA = pd.read_csv(cfg.db.irr_data, index_col=0)
WUI = pd.read_csv(cfg.db.wui, index_col=0)
Q_MAX = pd.read_csv(cfg.db.quota_before, index_col=0)
Q_MIN = pd.read_csv(cfg.db.quota_after, index_col=0)
KM_DEG = 111  # km / degree


def get_quota_from_data(
    data: pd.DataFrame, obj: BaseObj, time: TimeDriver
) -> float:
    """从数据中获取当月用水配额，根据面积转化成毫米形式"""
    res_x, res_y = obj.model.nature.major_layer.resolution
    # 1e8: 亿立方米 -> 立方米
    q_sum = (
        data.loc[f"C{obj.unique_id}", str(time.month)]
        * 1e8
        * ureg.Quantity("m**3")
    )
    AREA = round((res_x * KM_DEG) * (res_y * KM_DEG), 2) * ureg.Quantity(
        "km ** 2"
    )
    # convert water volume -> mm
    quota_mm = (q_sum / AREA).to("mm").magnitude
    weights = obj.farmers.array(obj.params.quota_weighted_by)
    if weights.sum():
        return quota_mm * weights / weights.sum()
    else:
        return np.repeat(quota_mm / len(weights), len(weights))


def get_from_csv_data(
    data: pd.DataFrame,
    obj: BaseObj,
    time: TimeDriver,
) -> pd.Series:
    """Dynamically read city's water use intensity from csv file"""
    index = data["Year"] == time.year
    data_tmp = data.loc[index].set_index("City_ID")
    return data_tmp.loc[f"C{obj.unique_id}", list(cfg.crops_id)]


class City(Actor):
    """每个城市的主体"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_dynamic_variable(
            name="lands",
            data=LANDS_DATA,
            function=get_from_csv_data,
        )
        self.add_dynamic_variable(
            name="wui",
            data=WUI,
            function=get_from_csv_data,
        )
        self.add_dynamic_variable(
            name="quota_max", data=Q_MAX, function=get_quota_from_data
        )
        self.add_dynamic_variable(
            name="quota_min", data=Q_MIN, function=get_quota_from_data
        )

    @property
    def wui(self) -> pd.Series:
        """用水强度"""
        return self.dynamic_var("wui")

    @property
    def farmers(self) -> ActorsList:
        """所关联的农民"""
        return self.linked_agents("farmer")

    def random_set_farmers(self) -> None:
        """根据自身的耕地情况，随机产生农民主体"""
        # 现在的农民
        farmers_now = self.linked_agents("farmer", strict=False)
        # 每类农民有多少个
        land_pattern = self.dynamic_var("lands")
        # 与当前的差值
        diff = land_pattern.sum() - len(farmers_now)
        if diff < 0:  # 如果当前农民更多，杀死它们
            farmers_now.random_choose(abs(diff)).trigger("die")
        elif diff > 0:  # 如果需要创建更多主体
            new_farmers = self.model.agents.create(Farmer, num=diff, city=self)
            new_farmers.trigger(
                "link_to",
                agent=self,
                link="farmer",
                mutual=True,
            )

    def shuffle_farmers(self) -> None:
        """打乱所有农民的种植作物"""
        # 与本城市关联的土地
        land_pattern = self.dynamic_var("lands")
        # num
        cells = self.linked_agents("city", land=True).random_choose(
            len(self.farmers), as_list=True
        )
        # for each split groups: add properties
        split_index = land_pattern.cumsum()[:-1]
        farmers_g = self.farmers.split(split_index)
        cells_g = cells.split(split_index)
        for i, (farmers, cells_) in enumerate(zip(farmers_g, cells_g)):
            crop = land_pattern.index.to_list()[i]
            for agent, cell in zip(farmers, cells_):
                agent.put_on(cell)
                agent.crop = crop

    def assign_quotas(self):
        """将配额分配给所有主体"""
        policy = self.model.institution
        # 1987年之前没有配额，最小可分配水量就是最大可分配水量
        if policy is None:
            quota_min = quota_max = self.dynamic_var("quota_max")
        # 1987年之后官方配额，但可以灵活
        elif policy == "87-WAS":
            quota_min = self.dynamic_var("quota_min")
            quota_max = self.dynamic_var("quota_max")
        # 1998年之后官方配额强制，最大可分配水量就是最小配额
        elif policy == "98-UBR":
            quota_min = quota_max = self.dynamic_var("quota_min")
        # 更新农民的属性
        self.farmers.update("quota_min", quota_min)
        self.farmers.update("quota_max", quota_max)


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
            return data.sel(time=time.start_time, method="nearest").to_numpy()

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
        kc = self.linked_attr(attr="kc", link="here")
        etc = (et0 * ks * kc).reshape(self.shape3d)
        self.apply_raster(etc, attr_name="ETc")


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
        # 城市是 GeoDataFrame 主体，创建并连接到它们所辖范围
        self.cities = self.create_agents_from_gdf(
            gdf=CITIES,
            unique_id="City_ID",
            agent_cls=City,
        )
        super().initialize()
        self.hydro.batch_link_by_geometry(geo_agents=self.cities, link="city")
