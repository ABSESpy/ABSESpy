#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import logging
from numbers import Number
from typing import Iterable, Tuple

import networkx as nx
import numpy as np
from prettytable import PrettyTable

from .agent_list import BaseAgentList
from .human import BaseHuman
from .main import MainMediator
from .nature import BaseNature
from .objects import BaseAgent
from .patch import Patch

logger = logging.getLogger("__name__")


class Actor(BaseAgent):
    def __init__(self, *args, **kwargs):
        self._on_earth: bool = False
        self.mediator: MainMediator = self.model.mediator
        self.human: BaseHuman = self.model.human
        self.nature: BaseNature = self.model.nature
        super().__init__(*args, **kwargs)

    @property
    def population(self) -> BaseAgentList:
        return self.model.agents[self.breed]

    @property
    def on_earth(self) -> bool:
        return self._on_earth

    @property
    def pos(self) -> Tuple[int, int]:
        if self.on_earth:
            return self.nature.positions[self]
        else:
            return None

    def require(self, var: str, **kwargs):
        patch_obj = self.mediator.transfer_require(self, var, **kwargs)
        return patch_obj

    def loc(self, patch, **kwargs):
        patch_obj = self.require(patch, **kwargs)
        if len(patch_obj.shape) == 2:
            return patch_obj[self.pos]
        elif len(patch_obj.shape) == 3:
            return patch_obj[:, self.pos[0], self.pos[1]]

    def alter_nature(self, patch: str, value: "int|float|bool") -> Patch:
        patch = self.require(patch)
        patch[self.pos] = value
        return patch

    def report(
        self,
        memory: int = 0,
        max_width: int = 30,
        decimal: int = 4,
        verbose: bool = False,
    ) -> PrettyTable:
        table = PrettyTable()
        # TODO more general
        # * Farmer: 5 has no attribute 'metrics'.
        for metric, evo in self.metrics.items():
            table.add_row([metric, evo.get(memory)])
        table.field_names = ["Var", "Value"]
        if verbose:
            for attr, val in self.__dict__.items():
                if attr in ("id", "type"):
                    continue
                if attr.startswith("_"):
                    continue
                table.add_row([attr, val])
        table.max_width = max_width
        table.title = f"{self.type} {self.id}:"
        table.float_format = f".{decimal}"
        return table

    def update(self, attr: str, val: any) -> None:
        if attr in self.metrics:
            self.metrics[attr].update(val)
        elif attr == "decision":
            self.decision.update(val)
        elif not hasattr(self, attr):
            raise KeyError(f"Attribute {attr} not found.")
        else:
            setattr(self, attr, val)

    def find_tutor(self, others, metric, how="best"):
        better = others.better(metric, than=self)
        if len(better) == 0:
            tutor = self
        else:
            if how == "best":
                better = others.better(metric, than=None)
                weights = None
            elif how == "diff":
                diff = better.diff(metric, self)
                weights = diff
            # elif how == "fermi":
            #     diff = better.diff(metric, self)
            #     weights = fermi_ruler(diff)
            else:
                raise ValueError(f"Unknown evolve strategy {how}.")
            tutor = better.random_choose(p=weights)
        self.tutor.update(tutor)
        return tutor


class LandOwner(Actor):
    def setup(self):
        super().setup()
        self._owned_land: Patch = None
        self._area: Number = None
        self.land_neighbors = BaseAgentList(self.model)

    @property
    def area(self):
        return self._area

    @property
    def owned_land(self):
        return self._owned_land

    @owned_land.setter
    def owned_land(self, value: "np.ndarray[bool]|bool"):
        name = f"land_of_{self.breed}<{self.id}>"
        self._owned_land = self.model.nature.create_patch(value, name=name)
        self._area = self.owned_land.sum() * self.owned_land.cell_area

    @property
    def __iter_lands__(self):
        return self.owned_land.cells

    def residents(self, breed: str = None):
        return self.model.nature.lookup_agents(self.owned_land, breed=breed)

    def mine(self, patch: str, apply: callable = None) -> np.ndarray:
        mine = self.require(patch)[self.owned_land]
        if apply is not None:
            return apply(mine)
        else:
            return mine

    def add_connections(self, graph: nx.Graph, agents: Iterable[Actor]):
        graph.add_edges_from([(self, agent) for agent in agents])

    def alter_nature(
        self, patch: str, value: "int|float|bool|Iterable", land=False
    ) -> None:
        if land:
            mask = self.owned_land
            patch = self.require(patch)
            patch.update(value, mask=mask)
        else:
            super().alter_nature(patch, value)

    def find_land_neighbors(self, ownerships, graph: nx.Graph = None) -> None:
        owned = self.owned_land
        mask = owned.arr.buffer() & ~owned
        neighbors_id = np.unique(ownerships[mask])
        neighbors = self.population.ids(neighbors_id)
        self.land_neighbors.extend(neighbors)
        self.add_connections(graph, neighbors)

    def find_tutor(self, metric, others=None, how="best"):
        if others is None:
            others = self.land_neighbors
        return super().find_tutor(others, metric, how)
