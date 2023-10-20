#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from typing import Callable, Dict, TypeAlias, Union

from omegaconf import DictConfig

from abses.actor import Actor

from .cells import PatchCell
from .container import AgentsContainer
from .links import LinkContainer
from .modules import CompositeModule, Module
from .sequences import ActorsList, Selection

Actors: TypeAlias = Union[ActorsList, Selection, Actor]
Trigger: TypeAlias = Union[str, Callable]


class HumanModule(Module):
    """基本的人类模块"""

    def __init__(self, model, name=None):
        Module.__init__(self, model, name)
        self._agents = AgentsContainer(model)
        self._collections: Dict[str, Selection] = DictConfig({})
        self._rules: Dict[str, Trigger] = DictConfig({})

    @property
    def agents(self) -> AgentsContainer:
        """agents container"""
        return self._agents

    def actors(self, name: str | None = None) -> ActorsList:
        """Different selections of agents"""
        if name is None:
            return self.agents.to_list()
        if name not in self._collections:
            raise KeyError(f"{name} is not defined.")
        selection = self._collections[name]
        return self.actors().select(selection)

    def _must_be_actor(self, actor: Actor) -> None:
        if not isinstance(actor, Actor):
            raise TypeError(
                f"Actor must be a subclass of Actor, instead of {type(actor)}."
            )

    def _must_be_cell(self, cell: PatchCell) -> None:
        if not isinstance(cell, PatchCell):
            raise TypeError(
                f"Cell must be a subclass of Cell, instead of {type(cell)}."
            )

    def define(self, name: str, selection: Selection) -> ActorsList:
        """定义一次主体查询"""
        if name in self._collections:
            raise KeyError(f"{name} is already defined.")
        selected = self.actors().select(selection)
        self._collections[name] = selection
        return selected


class BaseHuman(CompositeModule, HumanModule, LinkContainer):
    """基本的人类模块"""

    def __init__(self, model, name="human"):
        LinkContainer.__init__(self)
        HumanModule.__init__(self, model, name)
        CompositeModule.__init__(self, model, name=name)
