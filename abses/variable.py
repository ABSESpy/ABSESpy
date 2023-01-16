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
    """Singleton Registry for each model."""

    _model: Dict[int, VariablesRegistry] = {}
    _lock = threading.RLock()

    def __new__(cls: type[Self], model: Model) -> Self:
        instance = cls._model.get(model, None)
        if instance is None:
            instance = super().__new__(cls)
            with cls._lock:
                cls._model[model] = instance
        return instance

    def __init__(self, model: Model):
        self.model: Model = model
        self._variables: List[str] = []
        self._objs_registry: Dict[BaseObject, List[str]] = {}
        self._map: Dict[str, List[BaseObject]] = {}
        self._ln: Dict[str, str] = {}
        self._units: Dict[str, str] = {}
        self._data_types: Dict[str, Type] = {}
        self._checker: Dict[str, List[Callable]] = {}

    def _check_type(
        self, var_name: str, dtype: Type, error_when: Optional[bool] = False
    ) -> bool:
        """Judge if the given variable's type matches its given data."""
        dtype_now = self._data_types.get(var_name, None)
        if dtype_now is None:
            flag = None
        elif dtype is dtype_now:
            flag = True
        else:
            flag = False
        if flag is error_when:
            raise ValueError(
                f"Failed in checking type of variable: '{dtype_now}', now, inputting {dtype}"
            )
        return flag

    def _is_registered(
        self, var_name: str, error_when: Optional[bool] = None
    ) -> bool:
        """Judge if the given variable is registered."""
        if var_name in self._variables:
            flag = True
        else:
            flag = False
        if flag is True and error_when is True:
            raise ValueError(f"Variable {var_name} already registered.")
        elif flag is False and error_when is False:
            raise ValueError(f"Variable {var_name} hasn't been registered")
        else:
            return flag

    def _has_variable(
        self, owner, var_name, error_when: Optional[bool] = None
    ) -> bool:
        """Judge if the given variable is belong to a given owner."""
        if owner in self._objs_registry:
            flag = var_name in self._objs_registry[owner]
        else:
            flag = False
            self._objs_registry[owner] = []
        if flag is True and error_when is True:
            raise ValueError(
                f"Variable '{var_name}' has already been registered in '{owner}'."
            )
        elif flag is False and error_when is False:
            raise ValueError(
                f"'{owner}' does not have a registered variable '{var_name}'."
            )
        else:
            return flag

    def _add_variable(
        self,
        var_name: str,
        long_name: Optional[str] = None,
        units: Optional[str] = None,
        dtype: Optional[Type] = None,
        check_func: Optional[Iterable[Callable]] = None,
    ) -> None:
        self._is_registered(var_name, error_when=True)
        self._check_type(var_name, dtype=dtype, error_when=False)
        self._variables.append(var_name)
        self._map[var_name] = list()
        self._ln[var_name] = long_name
        self._units[var_name] = units
        self._data_types[var_name] = dtype
        self._checker[var_name] = make_list(check_func)

    def register(
        self, owner: BaseObject, var_name: str, *args, **kwargs
    ) -> None:
        if not self._is_registered(var_name):
            self._add_variable(var_name, *args, **kwargs)
        self._has_variable(owner, var_name, error_when=True)
        self._objs_registry[owner].append(var_name)
        self._map[var_name].append(owner)

    def check_variable(self, var_name: str, value: Any) -> bool:
        """
        Check if the given value is valid data registered variable.

        Args:
            var_name (str): variable's name.
            value (Any): data to check.

        Returns:
            bool: if the value is valid data, returns True.
        """
        results = []
        results.append(self._is_registered(var_name))
        results.append(
            self._check_type(var_name, type(value), error_when=None)
        )
        for checker in self._checker[var_name]:
            results.append(checker(value))
        return all(results)

    def delete_variable(
        self, var_name: str, owner: Optional[BaseObject] = None
    ) -> None:
        """
        Delete a variable from its owner registry.

        Args:
            name (str): name of the variable to be deleted.
            owner (Optional, BaseObject): owner of this variable.
        """

        def remove_var_from_owner(owner):
            owned_vars = self._objs_registry[owner]
            owned_vars.remove(var_name)
            self._map[var_name].remove(owner)
            if len(owned_vars) == 0:
                del self._objs_registry[owner]

        self._is_registered(var_name, error_when=False)
        if owner is not None:
            self._has_variable(
                owner=owner, var_name=var_name, error_when=False
            )
            remove_var_from_owner(owner)
        else:
            for owner in tuple(self._map[var_name]):
                remove_var_from_owner(owner)
        # no owner has this variable, delete it from the registry.
        if len(self._map[var_name]) == 0 or owner is None:
            self._variables.remove(var_name)
            del self._ln[var_name]
            del self._units[var_name]
            del self._data_types[var_name]
            del self._checker[var_name]
            del self._map[var_name]


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
