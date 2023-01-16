#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

import logging
import os
import threading
from collections import deque
from datetime import datetime
from functools import total_ordering
from numbers import Number
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Deque,
    Dict,
    Iterable,
    List,
    Optional,
    Self,
    Type,
    TypeAlias,
    Union,
)

import numpy as np
import pint
from agentpy.model import Model

from abses.log import Log

from .bases import Creation
from .patch import Patch, update_array
from .tools.func import make_list, wrap_opfunc_to

if TYPE_CHECKING:
    from .objects import BaseObject

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


class VariablesRegistry:
    _model: Dict[int, VariablesRegistry] = {}
    _lock = threading.RLock()

    def __new__(cls: type[Self], model: Model) -> Self:
        instance = cls._model.get(model, None)
        if instance is None:
            instance = super().__new__(cls)
            with cls._lock:
                cls._model[model] = instance
        return instance

    def __init__(self, model):
        self.model = model
        self._variables: List[str] = []
        self._objs_registry: Dict[BaseObject, List[str]] = {}
        self._map: Dict[BaseObject, List[str]] = {}
        self._ln: Dict[str, str] = {}
        self._units: Dict[str, str] = {}
        self._data_types: Dict[str, Type] = {}
        self._checker: Dict[str, List[Callable]] = {}

    def _check_type(self, name, value) -> bool:
        if type(value) is self._data_types[name]:
            return True

    def _is_registered(
        self, name: str, error_when: Optional[bool] = None
    ) -> bool:
        if name in self._variables:
            flag = True
        else:
            flag = False
        if flag is True and error_when is True:
            raise ValueError(f"Variable {name} already registered.")
        elif flag is False and error_when is False:
            raise ValueError(f"Variable {name} hasn't been registered")
        else:
            return flag

    def _has_variable(
        self, owner, name, error_when: Optional[bool] = None
    ) -> bool:
        if owner in self._objs_registry:
            flag = True
        else:
            flag = False
            self._objs_registry[owner] = []
        if flag is True and error_when is True:
            raise ValueError(
                f"Variable '{name}' has already been registered in {owner}."
            )
        elif flag is False and error_when is False:
            raise ValueError(
                f"'{owner}' does not have a registered variable '{name}'."
            )
        else:
            return flag

    def add_variable(
        self,
        name: str,
        long_name: Optional[str] = None,
        units: Optional[str] = None,
        dtype: Optional[Type] = None,
        check_func: Optional[Iterable[Callable]] = None,
    ):
        self._is_registered(name, error_when=True)
        self._ln[name] = long_name
        self._units[name] = units
        self._data_types[name] = dtype
        self._checker[name] = make_list(check_func)

    def register(self, owner: BaseObject, name: str, *args, **kwargs):
        if not self._is_registered(name):
            self.add_variable(name, *args, **kwargs)
        self._has_variable(owner, name, error_when=True)
        self._objs_registry[owner].append(name)

    def check_registry(self, name: str, value: Any) -> bool:
        results = []
        results.append(self._is_registered(name))
        results.append(self._check_type(name, value))
        for checker in self._checker[name]:
            results.append(checker(value))
        return all(results)

    def delete_variable(self, owner, name: str) -> None:
        self._is_registered(name, error_when=False)
        self._objs_registry[owner]
        self._variables.remove(name)
        del self._ln[name]
        del self._units[name]
        del self._data_types[name]
        del self._checker[name]


@total_ordering
class Variable:
    def __init__(
        self,
        now: Data,
        owner: Optional[BaseObject] = None,
        history: Iterable[Data] = None,
    ):
        # self.registry: VariablesRegistry = owner.registry
        self.data = now
        self.owner = owner
        self.history = history
        wrap_opfunc_to(self, "_data")

    # ----------------------------------------------------------------

    def __getattribute__(self, __name: str) -> Any:
        if __name.startswith("_"):
            return super().__getattribute__(__name)
        # using data explicit methods.
        elif callable(getattr(self._data, __name, None)):
            return getattr(self.data, __name)
        else:
            return super().__getattribute__(__name)

    def __lt__(self, other):
        return self.data < other

    def __eq__(self, other):
        return self.data == other

    def __repr__(self):
        return f"<[{self.owner}]Var: {self.data}>"

    # ----------------------------------------------------------------

    @property
    def data(self) -> Data:
        return self._data

    @data.setter
    def data(self, data: Data) -> None:
        # self.registry._check_dtype(data=data)
        self._data = data

    # ----------------------------------------------------------------

    # TODO processing before return
    def get_value(self) -> Data:
        return self.data


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
