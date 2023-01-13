#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

import logging
import os
from collections import deque
from datetime import datetime
from functools import cached_property, total_ordering
from numbers import Number
from typing import Deque, Optional, Type, TypeAlias, Union

import numpy as np
import pint
from agentpy.model import Model

from abses.log import Log

from .objects import Creation, Notice
from .patch import Patch, update_array
from .tools.func import wrap_opfunc_to

MAXLENGTH = 5  # todo move it into system settings.

logger = logging.getLogger(__name__)

Data: TypeAlias = Union[Number, str, np.ndarray, Patch]
T: TypeAlias = datetime


# TODO feature: merge this
def setup_registry(registry):
    """set up the given registry for use with pint_xarray
    Namely, it enables ``force_ndarray_like`` to make sure results are always
    duck arrays.
    Parameters
    https://github.com/xarray-contrib/pint-xarray/blob/0cd77e80a07c58895d0851b6fdf1af646cb5bc19/pint_xarray/accessors.py
    ----------
    registry : pint.UnitRegistry
        The registry to modify
    """
    if not registry.force_ndarray and not registry.force_ndarray_like:
        registry.force_ndarray_like = True

    return registry


# https://github.com/xarray-contrib/pint-xarray/blob/0cd77e80a07c58895d0851b6fdf1af646cb5bc19/pint_xarray/accessors.py
# default_registry = setup_registry(pint.get_application_registry())


@total_ordering
class Variable(Log, Creation):
    _created_variables = {}

    def __init__(
        self,
        name: str,
        long_name: Optional[str] = None,
        initial_value: Optional[Data] = None,
        unit: Optional[str] = None,
    ):
        Log.__init__(self, name=name)
        Creation.__init__(self)
        self._long_name: str = long_name
        self._time: Deque[T] = deque([], maxlen=MAXLENGTH)
        self._history: Deque[Data] = deque([], maxlen=MAXLENGTH)
        self._unit: Optional[str] = unit
        self._dtype: Optional[Type] = None
        self.data: Optional[Data] = initial_value

    # ----------------------------------------------------------------

    def __lt__(self, other):
        return self.data < other

    def __eq__(self, other):
        return self.data == other

    def __repr__(self):
        return f"<Var[{self.name}]: {self.data}>"

    def _detect_dtype(self, data: Data) -> type:
        if data is None:
            return None
        elif hasattr(data, "dtype"):
            return data.dtype
        else:
            return type(data)

    def _check_dtype(self, data: Data) -> None:
        dtype = self._detect_dtype(data)
        # TODO: restrict input data's type
        # if dtype not in (Number, str, np.ndarray, Patch):
        #     raise TypeError(f"{dtype} is not a valid Variable's data dtype.")
        if self.dtype is None:
            self._data = data
            self._dtype = dtype
            wrap_opfunc_to(self, "data")
        elif dtype != self.dtype:
            raise TypeError(
                f"Input {dtype} mismatches existing Variable's dtype {self.dtype}."
            )

    def _check_unit(self, unit: str):
        # TODO
        pass

    def notification(self, notice: Notice):
        super().notification(notice)
        # self._step_record()

    # ----------------------------------------------------------------

    @property
    def dtype(self):
        return self._dtype

    @property
    def long_name(self) -> str:
        return self._long_name

    @property
    def data(self) -> Data:
        return self._data

    @data.setter
    def data(self, data: Data) -> None:
        self._check_dtype(data=data)
        self._data = data


class FileVariable(Variable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._filepath = None
        self._engine = None

    @property
    def path(self):
        return self._filepath

    def _file_is_existing(self, filepath: str) -> bool:
        return os.path.exists(filepath)
