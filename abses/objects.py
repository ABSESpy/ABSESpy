#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

import mesa

from abses.time import TimeDriver

from .bases import _Observer
from .components import _Component
from .dynamic import _DynamicVariable

if TYPE_CHECKING:
    from abses.main import MainModel


class _BaseObj(_Observer, _Component):
    """
    Base class for model's objects.
    Model object's have access to global model's parameters and time driver.
    """

    def __init__(
        self,
        model: MainModel,
        observer: Optional[bool] = True,
        name: Optional[str] = None,
    ):
        _Component.__init__(self, model=model, name=name)
        if observer:
            model.attach(self)
        self._model = model
        self._dynamic_variables: Dict[str, _DynamicVariable] = {}

    @property
    def time(self) -> TimeDriver:
        """Returns read-only model's time driver.

        Returns:
            _TimeDriver:
                Model's time driver.
        """
        return self.model.time

    @property
    def model(self) -> MainModel:
        """Returns read-only model object.

        Returns:
            MainModel:
                ABSES model object.
        """
        return self._model

    @property
    def dynamic_variables(self) -> Dict[str, Any]:
        """Returns read-only model's dynamic variables.

        Returns:
            Dict[str, Any]:
                Dictionary of model's dynamic variables.
        """
        if not self._dynamic_variables:
            return {}
        for k, v in self._dynamic_variables.items():
            return {k: v.now()}

    @model.setter
    def model(self, model: MainModel):
        """Sets the model object.

        Parameters:
            model : MainModel
                ABSES model object.
        """
        if not isinstance(model, mesa.Model):
            raise TypeError("Model must be an instance of mesa.Model")
        self._model = model

    def add_dynamic_variable(
        self, name: str, data: Any, function: Callable
    ) -> None:
        """Adds new dynamic variable.

        Parameters:
            name:
                Name of the variable.
            data:
                Data source for callable function.
            function:
                Function to calculate the dynamic variable.
        """
        var = _DynamicVariable(
            obj=self, name=name, data=data, function=function
        )
        self._dynamic_variables[name] = var

    def dynamic_var(self, attr_name: str) -> Any:
        """Returns output of a dynamic variable.

        Parameters:
            attr_name:
                Dynamic variable's name.
        """
        return self._dynamic_variables[attr_name].now()
