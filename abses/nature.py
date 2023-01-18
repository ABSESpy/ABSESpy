#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from typing import List, Tuple

import numpy as np
from agentpy.grid import AgentIter, Grid, _IterArea

from .algorithms.spatial import points_to_polygons, polygon_to_mask
from .container import AgentsContainer, BaseAgentList, apply_agents
from .factory import PatchFactory
from .modules import CompositeModule
from .patch import Patch
from .tools.func import norm_choice


class BaseNature(CompositeModule, PatchFactory, Grid):
    def __init__(self, model, name="nature", **kwargs):
        CompositeModule.__init__(self, model, name=name)
        PatchFactory.__init__(self, **kwargs)
        self._patches = {}  # TODO: refactor this

    @property
    def patches(self):
        return tuple(self._patches.keys())

    def set_space(self, shape, mask, *args, **kwargs):
        Grid.__init__(self, model=self.model, shape=shape, *args, **kwargs)
        self._mask = mask
        self.shape = shape
        # todo: refactor this
        if hasattr(mask, "coords"):
            self._coords = self.mask.coords
            self.inheritance = "_coords"

    def from_boundary(self, boundary, *args, **kwargs):
        shape = boundary.shape
        mask = ~boundary.interior
        self.set_space(shape, mask, *args, **kwargs)

    def send_patch(self, attr: str, **kwargs) -> Patch:
        if hasattr(self, attr):
            obj = getattr(self, attr)
            return obj
        elif attr in self.patches:
            module = self._patches[attr]
            obj = module.get_patch(attr, **kwargs)
            return obj
        else:
            raise ValueError(f"Unknown patch {attr}.")

    def initialize(self):
        settings = self.params.get("boundary")
        if settings:
            boundary = self.generate_boundary(settings)
            self.from_boundary(boundary)
        self.notify()

    def transfer_var(self, sender: object, var: str) -> None:
        if var not in self.patches:
            self._patches[var] = sender
        else:
            module = self._patches[var]
            if sender is module:
                self.logger.warning(
                    f"Transfer exists {var} of {module}, please use 'update' function to do so."
                )
            self.logger.error(
                f"{sender} wants to transfer an exists var '{var}', which was created by {module}!"
            )

    def transfer_update(
        self, sender: object, patch_name: str, **kwargs
    ) -> None:
        # update a patch
        if patch_name in self.patches:
            owner = self._patches[patch_name]
            getattr(owner, patch_name).update(**kwargs)
            self.logger.debug(
                f"{sender} requires {patch_name} of {owner} to update."
            )

    def random_positions(
        self,
        k: int,
        mask: np.ndarray = None,
        probabilities: np.ndarray = None,
        only_empty: bool = False,
    ) -> List[Tuple[int, int]]:
        """
        Choose 'k' patches in the world randomly.

        Args:
            k (int): number of patches to choose.
            mask (np.ndarray, optional): bool mask, only True patches can be choose. If None, all patches are accessible. Defaults to None.
            replace (bool, optional): If a patch can be chosen more than once. Defaults to False.

        Returns:
            List[Tuple[int, int]]: iterable coordinates of chosen patches.
        """
        if mask is None:
            mask = np.ones(self.shape, bool)
        if only_empty is True:
            mask = mask & ~self.has_agent()
        mask = self.create_patch(mask, "mask")
        accessible_pos = [(x, y) for x, y in mask.arr.where()]
        if probabilities is not None:
            probabilities = probabilities[mask]
        pos_index = norm_choice(
            np.arange(len(accessible_pos)), size=k, p=probabilities
        )
        positions = [accessible_pos[i] for i in pos_index]
        return positions

    def random_move(
        self,
        agent,
        only_empty: bool = True,
        avoid_breed: str = None,
        only_accessible: bool = True,
    ):
        mask = self.create_patch(True, "mask")
        if only_accessible:
            mask = mask | self.accessible
        if only_empty:
            mask = mask | ~self.has_agent(avoid_breed)
        pos = self.random_positions(1, mask)[0]
        self.move_to(agent, pos)

    @apply_agents
    def add_agents(
        self,
        agents=None,
        positions=None,
        random=False,
        empty=False,
        only_accessible=True,
    ):
        # TODO: refactor this without if-else
        if only_accessible:
            mask = self.accessible
            positions = self.random_positions(
                len(agents),
                mask=mask,
            )
            super().add_agents(agents, positions=positions)
        else:
            super().add_agents(
                agents,
                positions=positions,
                random=random,
                empty=empty,
            )
        agents._on_earth = True
        self.logger.info(
            f"Randomly placed {len(agents)} '{agents.breed()}' in nature."
        )

    def land_allotment(
        self, agents, mask: np.ndarray = None
    ) -> AgentsContainer:
        """
        > For each cell in the grid, find the nearest agent and assign that agent's id to the cell

        :param mask: a boolean array that indicates which cells should be assigned an owner
        :return: The pattern of the agents.
        """
        ownership = self.create_patch(
            np.nan,
            name=f"{agents.breed()}s_ownership",
        )  # TODO: add=True, refactor patches
        if mask is None:
            mask = self.accessible
        points = agents.array("pos")
        polygons = points_to_polygons(points)
        for i, agent in enumerate(agents):
            owned_land = polygon_to_mask(polygons[i], shape=self.shape)
            owned_land = owned_land & mask
            ownership.update(agent.id, mask=owned_land)
            agent.owned_land = owned_land
        self.__setattr__(ownership.name, ownership)
        return ownership

    def lookup_agents(
        self, mask_patch: Patch, breed: str = None
    ) -> AgentsContainer:
        # TODO 如何不查找到已经死掉的 Agents？？
        area = np.array(
            [self.grid.agents[cell] for cell in mask_patch.arr.where()],
            dtype=object,
        )
        agents_lst = AgentIter(self.model, _IterArea(area)).to_list()
        agents = AgentsContainer(model=self.model, agents=agents_lst)
        if breed is None:
            return agents
        else:
            return agents.get_breed(breed)

    def find_neighbor_by_position(
        self,
        pos: Tuple[int, int],
        distance: int = 0,
        neighbors: int = 4,
        breed: str = None,
    ) -> "AgentsContainer|BaseAgentList":
        position = self.create_patch(False, "position")
        position[pos] = True
        buffer = position.arr.buffer(buffer=distance, neighbors=neighbors)
        return self.lookup_agents(buffer, breed=breed)

    def has_agent(self, breed: str = None, mask: Patch = None) -> Patch:
        if mask is None:
            mask = self.create_patch(True, "mask")
        if breed is None:
            agents = self.agents.to_list()
        else:
            agents = self.agents[breed]
        has_agents = np.zeros(self.shape, bool)
        for agent in agents.select(agents.on_earth):
            has_agents[agent.pos] = True
        patch = self.create_patch(has_agents, "has_agent", True)
        return patch
