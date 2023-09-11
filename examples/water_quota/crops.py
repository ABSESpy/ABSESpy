#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional

import pandas as pd
import yaml

POINTS = ("start", "ini", "dev", "mid", "end")


@dataclass
class Crop:
    index: int
    height: float
    start: datetime
    ini: datetime
    dev: datetime
    mid: datetime
    end: datetime
    Kc_ini: float
    Kc_mid: float
    Kc_end: float
    name_ch: str = None
    name_en: str = None
    _year: int = 1990
    _language: str = "en"
    _pattern: str = r"%Y-%m-%d"
    _attrs: dict = field(default_factory={})

    def __repr__(self):
        return f"<{self.name} ({self.index})>"

    @classmethod
    def load_from(cls, path: str, suffix: Optional[str] = "yaml"):
        # Check if file path is valid
        try:
            with open(path, "r", encoding="utf8") as f:
                if suffix == "yaml":
                    # Load data from YAML file into dictionary
                    data = yaml.safe_load(f)
                elif suffix == "json":
                    # Load data from JSON file into dictionary
                    data = json.load(f)
                else:
                    raise ValueError(f"Invalid format: {suffix}")
        except IOError as exc:
            raise IOError(f"Cannot open file: {path}") from exc

        # Create instance of class using dictionary as input
        return cls.create(**data)

    @classmethod
    def create(cls, *args, **kwargs):
        attrs = {
            key: kwargs.pop(key, None)
            for key in list(kwargs.keys())
            if key not in cls.__init__.__code__.co_varnames
        }
        return cls(*args, **kwargs, _attrs=attrs)

    @property
    def attrs(self):
        return self._attrs

    @property
    def name(self):
        if self.lang == "ch":
            return self.name_ch
        elif self.lang == "en":
            return self.name_en

    @property
    def lang(self):
        return self._language

    @property
    def Lini(self):
        return (self.ini - self.start).days

    @property
    def year(self):
        return self._year

    @year.setter
    def year(self, year):
        y_now = self.year
        for point in POINTS:
            dt = self.__getattribute__(point)
            y_new = year + (dt.year - y_now)
            new_dt = datetime(y_new, dt.month, dt.day)
            self.__setattr__(point, new_dt)
        self._year = year

    def points(
        self,
        ini: float = None,
        mid: float = None,
        end: float = None,
        dictionary: Dict[str, float] = None,
    ) -> pd.Series:
        """
        Crucial phenological points of this crop.

        Args:
            ini (float, optional): Kc in the initial stage. Defaults to None.
            mid (float, optional): Kc in the middle stage. Defaults to None.
            end (float, optional): Kc in the end stage. Defaults to None.
            points (_type_, optional): a dictionary where 'ini' and 'mid', and 'end' saved. Defaults to None. Priority: extract kwargs firstly, then use dictionary, finally use the reference value.
        Returns:
            pd.Series: five points of the critical phenological points saved as [PeriodIndex][Kc-value] format Pandas Series:
                1. start of the initial stage,
                2. start of the quick developing stage,
                3. start of the middle stage,
                4. start of the end stage
                5. final end  period index
            more information of regarding the five stages can be found at Single crop coefficient (Kc) document at the FAO56 website: https://www.fao.org/3/x0490e/x0490e0b.htm.
        """
        x = [getattr(self, p) for p in POINTS]
        index = pd.PeriodIndex(pd.to_datetime(x), freq="D")
        tmp_points = {"ini": ini, "mid": mid, "end": end}
        if dictionary is None:
            dictionary = {}
        for k, v in tmp_points.items():
            if v is not None:
                dictionary[k] = v
        ini = dictionary.get("ini", self.Kc_ini)
        mid = dictionary.get("mid", self.Kc_mid)
        end = dictionary.get("end", self.Kc_end)
        y = [ini, ini, mid, mid, end]
        return pd.Series(y, index=index, name="Kc")

    def curve(
        self,
        freq: Optional[str] = "D",
        full: Optional[bool] = False,
        **kwargs,
    ) -> pd.Series:
        """
        Interpolate critical points into the phenological curve.

        Args:
            freq (str, optional): time resolution, this method recognizes the same directives as the [.strftime()](https://pandas.pydata.org/docs/reference/api/pandas.Period.strftime.html) function of the Pandas package. Defaults to "D".

        Returns:
            pd.Series: rescaled phenological curve saved as [PeriodIndex][Kc-value] format Pandas Series.
        """
        series = self.points(**kwargs).resample("D").asfreq(freq).interpolate()
        series = series.resample(freq).mean()
        if full:
            full_index = pd.period_range(
                f"{self.year}-01-01", f"{self.year}-12-31", freq=freq
            )
            full_series = pd.Series(0.0, index=full_index)
            full_series.loc[series.index] = series
            return full_series
        else:
            return series
