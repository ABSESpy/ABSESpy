#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from typing import List, Optional, Tuple, Union, overload

import numpy as np
from agentpy.grid import AgentSet, Grid

from abses.actor import Actor
from abses.boundary import Boundaries
from abses.geo import Geo

from .algorithms.spatial import points_to_polygons, polygon_to_mask
from .container import ActorsList, AgentsContainer
from .factory import PatchFactory
from .modules import CompositeModule
from .patch import Patch, get_buffer
from .tools.func import norm_choice

DEFAULT_WORLD = {
    "width": 9,
    "height": 9,
    "resolution": 10,
    # 'units': 'm',
}


class PositionSet(AgentSet):
    def __init__(self, model, index, accessible, *args, **kwargs):
        super().__init__(model, *args, **kwargs)
        self._index: Tuple[int, int] = index
        self._accessible: bool = accessible

    @property
    def index(self):
        return self._index

    @property
    def accessible(self):
        return self._accessible

    def add(self, actor: Actor):
        if self._accessible is False:
            raise KeyError(f"{self.index} is not accessible.")
        else:
            super().add(actor)


class BaseNature(CompositeModule, PatchFactory):
    def __init__(self, model, name="nature", **kwargs):
        CompositeModule.__init__(self, model, name=name)
        PatchFactory.__init__(self, model=model, **kwargs)
        self._boundary: Boundaries = None
        self._grid: np.ndarray = None

    # @property
    # def patches(self):
    #     return tuple(self._patches.keys())

    def __getitem__(self, key: Union[Tuple[int, int], slice]) -> ActorsList:
        items = self.grid[key]
        if isinstance(items, AgentSet):
            return ActorsList(self.model, items)
        else:
            agents = ActorsList(self.model)
            for item in items.flatten():
                agents.extend(item)
        return agents

    @property
    def boundary(self):
        return self._boundary

    @boundary.setter
    def boundary(self, boundary):
        self._boundary = boundary

    @property
    def grid(self) -> np.ndarray:
        return self._grid

    def _setup_grid(self, shape: Tuple[int, int]):
        array = np.empty(shape=shape, dtype=object)
        it = np.nditer(array, flags=["refs_ok", "multi_index"])
        for _ in it:
            index = it.multi_index
            access = self.accessible[index]
            array[index] = PositionSet(
                model=self.model, accessible=access, index=index
            )
        self._grid = array

    def _after_parsing(self):
        settings = self.params.get("world", DEFAULT_WORLD).copy()
        self.geo.auto_setup(settings=settings)
        boundary_settings = self.params.get("boundary", {})
        self.boundary = Boundaries(shape=self.geo.shape, **boundary_settings)
        self._setup_grid(shape=self.geo.shape)

    # def send_patch(self, attr: str, **kwargs) -> Patch:
    #     if hasattr(self, attr):
    #         obj = getattr(self, attr)
    #         return obj
    #     elif attr in self.patches:
    #         module = self._patches[attr]
    #         obj = module.get_patch(attr, **kwargs)
    #         return obj
    #     else:
    #         raise ValueError(f"Unknown patch {attr}.")

    # def transfer_var(self, sender: object, var: str) -> None:
    #     if var not in self.patches:
    #         self._patches[var] = sender
    #     else:
    #         module = self._patches[var]
    #         if sender is module:
    #             self.logger.warning(
    #                 f"Transfer exists {var} of {module}, please use 'update' function to do so."
    #             )
    #         self.logger.error(
    #             f"{sender} wants to transfer an exists var '{var}', which was created by {module}!"
    #         )

    # def transfer_update(
    #     self, sender: object, patch_name: str, **kwargs
    # ) -> None:
    #     # update a patch
    #     if patch_name in self.patches:
    #         owner = self._patches[patch_name]
    #         getattr(owner, patch_name).update(**kwargs)
    #         self.logger.debug(
    #             f"{sender} requires {patch_name} of {owner} to update."
    #         )

    def random_positions(
        self,
        k: int,
        where: np.ndarray = None,
        probabilities: np.ndarray = None,
        only_empty: bool = False,
        replace: bool = False,
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
        if where is None:
            where = self.accessible
        else:
            where = self.accessible & where
        if only_empty is True:
            where = where & ~self.has_agent()
        where = self.create_patch(where, "where")
        potential_pos = [(x, y) for x, y in where.arr.where()]
        if probabilities is not None:
            probabilities = probabilities[where]
        pos_index = norm_choice(
            np.arange(len(potential_pos)),
            size=k,
            p=probabilities,
            replace=replace,
        )
        positions = [potential_pos[i] for i in pos_index]
        return positions

    # def random_move(
    #     self,
    #     agent,
    #     only_empty: bool = True,
    #     avoid_breed: str = None,
    #     only_accessible: bool = True,
    # ):
    #     mask = self.create_patch(True, "mask")
    #     if only_accessible:
    #         mask = mask | self.accessible
    #     if only_empty:
    #         mask = mask | ~self.has_agent(avoid_breed)
    #     pos = self.random_positions(1, mask)[0]
    #     self.move_to(agent, pos)

    def add_agents(
        self,
        agents: ActorsList,
        positions=None,
    ):
        if positions is None:
            positions = self.random_positions(len(agents))
        for agent, pos in zip(agents, positions):
            agent.settle_down(position=pos)
            self.grid[pos].add(agent)
        # msg = f"Randomly placed {len(agents)} '{agents.breed()}' in nature."
        # self.mediator.transfer_event(self, msg)

    def land_allotment(
        self, agents: ActorsList, where: np.ndarray = None
    ) -> AgentsContainer:
        """
        > For each cell in the grid, find the nearest agent and assign that agent's id to the cell

        :param mask: a boolean array that indicates which cells should be assigned an owner
        :return: The pattern of the agents.
        """
        where = self.geo.wrap_data(where, masked=True)
        points = agents.array("pos")
        polygons = points_to_polygons(points)
        for i, agent in enumerate(agents):
            owned_land = polygon_to_mask(polygons[i], shape=self.shape)
            owned_land = owned_land & where
            agent.attach_places(name="owned", place=owned_land)

    def lookup_agents(
        self, where: np.ndarray, breed: Optional[str] = None
    ) -> ActorsList:
        """
        Find alive agents who is settling on the given patch.

        Args:
            mask_patch (NDArray[Bool]): bool masked, must has the same shape as the world.
            breed (Optional[str], optional): only search the designated breed. Defaults to None.

        Returns:
            ActorsList: actors on the given patches.
        """
        where = self.create_patch(where, "where")
        agents = ActorsList(model=self.model)
        for cell in where.arr.where():
            agents_here = self.grid[cell]
            agents.extend(agents_here)
        if breed is None:
            return agents
        else:
            return agents.to_dict()[breed]

    def find_neighbor_by_position(
        self,
        pos: Tuple[int, int],
        distance: int = 0,
        neighbors: int = 4,
        breed: str = None,
    ) -> ActorsList:
        position = np.zeros(self.shape, dtype=bool)
        position[pos] = True
        buffer = get_buffer(buffer=distance, neighbors=neighbors)
        return self.lookup_agents(buffer, breed=breed)

    def has_agent(
        self, breed: str = None, where: Optional[np.ndarray] = None
    ) -> Patch:
        """
        Where exists agents.

        Args:
            breed (str, optional): if assigned, only find this type of agents. Defaults to None.
            mask (np.ndarray, optional): if assigned, only find agents on those patches. Defaults to None.

        Returns:
            Patch: bool patch, True if this cell has agent, False otherwise.
        """
        where = self.geo.wrap_data(where, masked=True)
        agents = self.lookup_agents(where, breed=breed)
        has_agents = np.zeros(self.shape, bool)
        for agent in agents.select(agents.on_earth):
            has_agents[agent.pos] = True
        patch = self.create_patch(has_agents, "has_agent", True)
        return patch
