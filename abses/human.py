#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from typing import Callable, Dict, Optional, TypeAlias, Union

import networkx as nx
from agentpy import AttrDict

from abses.actor import Actor

from .container import AgentsContainer
from .modules import CompositeModule, Module
from .sequences import ActorsList, Selection

Actors: TypeAlias = Union[ActorsList, Selection, Actor]
Trigger: TypeAlias = Union[str, Callable]


class HumanModule(Module):
    def __init__(self, model, name=None):
        super().__init__(model, name)
        self._agents = AgentsContainer(model)
        self._collections: Dict[str, Selection] = AttrDict()
        self._rules: Dict[str, Trigger] = AttrDict()

    def __getattr__(self, name):
        if name[0] == "_":
            return super().__getattr__(name)
        elif name in self._collections:
            selection = self._collections[name]
            return self.actors.select(selection)
        else:
            return super().__getattr__(name)

    @property
    def agents(self) -> AgentsContainer:
        return self._agents

    @property
    def actors(self) -> ActorsList:
        return self.agents.to_list()

    def define(self, name: str, selection: Selection) -> ActorsList:
        selected = self.actors.select(selection)
        self._collections[name] = selection
        return selected

    # def rule(self, actors: Actors, when: Selection, then: Trigger, name: Optional[str] = None):
    #     if name is None:
    #         pass
    #     self.define(name=name)
    #     actors_to_trigger = actors.select(when)
    #     results = actors_to_trigger.trigger(then)
    #     return actors_to_trigger, results

    def arena(self, actor_A: Actors, actor_B: Actors, interaction: Trigger):
        actor_A.trigger(interaction, actor_B)
        actor_B.trigger(interaction, actor_A)

    def require(self, attr: str) -> object:
        return self.mediator.transfer_require(self, attr)


class BaseHuman(CompositeModule, HumanModule):
    def __init__(self, model, name="human"):
        HumanModule.__init__(self, model, name)
        CompositeModule.__init__(self, model, name=name)


#     def mock(self, agents, attrs, how="attr"):
#         tutors = self.to_agents(agents.tutor.now)
#         for attr in make_list(attrs):
#             values = tutors.array(attr, how)
#             agents.update(attr, values)


# def skip_if_close(func):
#     def skip_module_method(self, *args, **kwargs):
#         if self.opening:
#             func(self, *args, **kwargs)
#         else:
#             if self.log_flag:
#                 self.logger.warning(f"{self}.")

#     return skip_module_method
