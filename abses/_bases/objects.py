#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

import mesa
from loguru import logger

from abses._bases.bases import _Observer
from abses._bases.components import _Component
from abses._bases.dynamic import _DynamicVariable
from abses.time import TimeDriver

if TYPE_CHECKING:
    from abses.main import MainModel


class _BaseObj(_Observer, _Component):
    """
    Base class for model's objects.
    Model object's have access to global model's parameters and time driver.
    """

    def __init__(
        self,
        model: MainModel[Any, Any],
        observer: Optional[bool] = True,
        name: Optional[str] = None,
    ):
        _Component.__init__(self, model=model, name=name)
        if observer:
            model.attach(self)
        self._model = model
        self._dynamic_variables: Dict[str, _DynamicVariable] = {}
        self._updated_ticks: List[int] = []

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

    @property
    def dynamic_variables(self) -> Dict[str, _DynamicVariable]:
        """Returns read-only model's dynamic variables.

        Returns:
            Dict[str, Any]:
                Dictionary of model's dynamic variables.
        """
        return self._dynamic_variables

    def add_dynamic_variable(
        self, name: str, data: Any, function: Callable, **kwargs
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
            obj=self, name=name, data=data, function=function, **kwargs
        )
        self._dynamic_variables[name] = var
        logger.info(f"Added dynamic variable '{var}'.")

    def dynamic_var(self, attr_name: str) -> Any:
        """Returns output of a dynamic variable.

        Parameters:
            attr_name:
                Dynamic variable's name.
        """
        if self.time.tick in self._updated_ticks:
            return self._dynamic_variables[attr_name].cache
        return self._dynamic_variables[attr_name].now()
