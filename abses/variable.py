#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import logging
import os
from collections import deque
from functools import cached_property, total_ordering
from numbers import Number
from typing import Deque, Optional, TypeAlias, Union

import numpy as np
import pint
from agentpy.model import Model

from .objects import BaseObj
from .patch import Patch, update_array
from .tools.func import warp_opfunc

MAXLENGTH = 5  # todo move it into system settings.

logger = logging.getLogger(__name__)

Data: TypeAlias = Union[Number, str, np.ndarray, Patch]


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


# def binary_operator(cls):
#     """Class decorator that rewrite operator methods."""


#     for opname in _convert:
#         opfunc = getattr(cls, opname)
#         setattr(cls, opname, warp_func(opfunc))
#     return cls


_convert = (
    "__neg__",
    "__pos__",
    "__abs__",
    "__invert__",
    "__add__",
    "__sub__",
    "__mul__",
    "__truediv__",
    "__floordiv__",
    "__mod__",
    "__divmod__",
    "__pow__",
    "__lshift__",
    "__rshift__",
    "__and__",
    "__xor__",
    "__or__",
    "__lt__",
    "__le__",
    "__eq__",
    "__be__",
    "__gt__",
    "__ge__",
)


# @binary_operator
class Variable(BaseObj):
    _created_variables = {}

    def __init__(
        self,
        model: Model,
        name: str,
        long_name: Optional[str] = None,
        initial_value: Optional[Data] = None,
        unit: Optional[str] = None,
    ):
        super().__init__(model=model, name=name, observer=True)
        self._long_name: str = long_name
        self._history: Deque = deque([], maxlen=MAXLENGTH)
        self._unit: Optional[str] = unit
        self.data: Data = initial_value

    def _setup_opfunc(self, data: any):
        for opname in _convert:
            opfunc = getattr(data.__class__, opname, None)
            if opfunc is not None:
                setattr(self.__class__, opname, warp_opfunc(opfunc))

    # def __repr__(self):
    #     return f"<Variable [{self.name}] ({self.dtype})>"

    def _detect_dtype(self, data: Data) -> type:
        if hasattr(data, "dtype"):
            return data.dtype
        else:
            return type(data)

    def _check_unit(self, unit: str):
        # TODO finish this
        pass

    @cached_property
    def dtype(self) -> type:
        return self._detect_dtype(self._data)

    @classmethod
    def _is_new_var(cls, name: str) -> bool:
        if name in cls._created_variables:
            logger.warn(f"{name} already exists.")
            return False
        else:
            return True

    @classmethod
    def create(cls, name, *args, **kwargs):
        if cls._is_new_var(name):
            variable = cls(name, *args, **kwargs)
        cls._created_variables[name] = variable
        return variable

    # @classmethod
    # def from_xarray(cls, data, *args, **kwargs):
    #     name = getattr(data, "name", None)
    #     variable = cls.create(name=name, *args, **kwargs)
    #     variable.data = data
    #     return variable

    @property
    def long_name(self) -> str:
        return self._long_name

    @property
    def data(self) -> Data:
        return self._data

    @data.setter
    def data(self, data: Data) -> None:
        self._detect_dtype(data)
        self._data = data
        self._setup_opfunc(data)


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
