#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Optional, Set, Union

from omegaconf import DictConfig

from .tools.func import make_list

if TYPE_CHECKING:
    from abses.main import MainModel


class _Component:
    """
    Class _Component is used to represent a component of the model. Extends _Log class to be able to log any issues.
    Components are foundational pieces in constructing the model's entities.
    It is initialized with a model and a optional name.
    """

    __args__ = []

    def __init__(self, model: MainModel, name: Optional[str] = None):
        self._args: Set[str] = set()
        self._model = model
        self.name = name
        self.add_args(self.__args__)

    @property
    def name(self) -> str:
        """Get the name of the component"""
        return self._name

    @name.setter
    def name(self, value: None | str) -> None:
        """Set the name of the component"""
        if value is None:
            value = self.__class__.__name__.lower()
        self._name = value

    @property
    def params(self) -> dict:
        """Returns read-only model's parameters.

        Returns:
        ___________
        dict:
            Dictionary of model's parameters.
        """
        return self._model.settings.get(self.name, DictConfig({}))

    @property
    def args(self) -> DictConfig:
        """Returns read-only component's arguments.

        Returns
        -------
        DictConfig
            Component's arguments dictionary.
        """
        return DictConfig({arg: self.params[arg] for arg in self._args})

    def add_args(self, args: Union[str, Iterable[str]]) -> None:
        """Add model's parameters as component's arguments.

        Parameters
        ----------
        args : Union[str, Iterable[str]]
            Model's parameters to be added as component's arguments.

        Returns
        _______
        None
        """
        args_set = set(make_list(args))
        for arg in args_set:
            if arg not in self.params:
                raise KeyError(f"Argument {arg} not found.")
            self._args.add(arg)
