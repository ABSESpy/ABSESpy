#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Optional, Set, Union

from omegaconf import DictConfig

from .log import _Log
from .tools.func import make_list

if TYPE_CHECKING:
    from abses.main import MainModel


class _Component(_Log):
    """
    Class _Component is used to represent a component of the model. Extends _Log class to be able to log any issues.
    This class helps to designate certain parameters of the model as components and handle them separately.
    It is initialized with a model and a optional name.
    """

    __args__ = []

    def __init__(self, model: MainModel, name: Optional[str] = None):
        """
        Initialize component. A component is a foundational element of the model's entities.
        A component will take the model's parameters as arguments so as to not overwrite them.
        """
        _Log.__init__(self, name=name)
        self._args: Set[str] = set()
        self._model = model
        self.add_args(self.__args__)

    @property
    def params(self) -> dict:
        """Returns the model's parameters.

        Parameters:
        ___________
        None

        Returns:
        ___________
        dict:
            Dictionary of model's parameters.
        """
        return self._model.settings.get(self.name, DictConfig({}))

    @property
    def args(self) -> DictConfig:
        """Returns component's arguments.

        Parameters
        ----------
        None

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
