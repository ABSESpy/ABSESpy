#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
This script is used to manipulate actors' movements.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

import mesa_geo as mg
from mesa.space import Coordinate

from abses.errors import ABSESpyError

if TYPE_CHECKING:
    from abses.actor import Actor
    from abses.cells import PatchCell
    from abses.nature import PatchModule


def _get_layer_and_position(
    pos: Coordinate | PatchCell, layer: Optional[PatchModule] = None
) -> Tuple[Coordinate, PatchModule]:
    if isinstance(pos, mg.Cell):
        if layer is not None and layer is not pos.layer:
            raise ABSESpyError(
                "The input layer is not consistent with the cell's layer."
            )
        return pos.layer, pos.pos
    if isinstance(pos, tuple) and len(pos) == 2:
        return layer, pos
    raise TypeError(f"Invalid position type {pos}.")


def _put_agent_on_cell(agent: Actor, cell: PatchCell) -> None:
    """
    This function is used to put an agent on a cell.
    """
    if not isinstance(cell, mg.Cell):
        raise TypeError(
            f"Agent must be put on a `abses.PatchCell`, instead of {type(cell)}"
        )
    if agent.on_earth:
        agent.move.off()
    cell.agents.add(agent, register=True)
    agent.at = cell
    # self.geometry = Point(cell.layer.transform * cell.indices)


def move_agent_to(
    agent: Actor,
    layer: PatchModule,
    pos: Coordinate | mg.Cell,
) -> bool:
    """Move an Actor to another position of this layer.

    Parameters:
        agent:
            The actor to operate.
        position:
            The position to put on.

    Raises:
        ABSESpyError:
            If the agent is not located at this layer before moving.

    Returns:
        If the operation is successful.
    """
    expected_layer, pos = _get_layer_and_position(pos)
    if not isinstance(layer, mg.RasterLayer):
        raise TypeError(f"{layer} is not mg.RasterLayer.")
    if expected_layer and expected_layer is not layer:
        raise ABSESpyError(
            f"{pos} expects operation on the layer {expected_layer}, got input {layer}."
        )
    if layer.out_of_bounds(pos):
        raise ValueError(f"Position {pos} is out of bounds.")
    cell = layer.cells[pos[0]][pos[1]]
    _put_agent_on_cell(agent, cell)


class _Movements:
    """
    This class is used to manipulate actors' movements.
    """

    def __init__(self, actor: Actor) -> None:
        self.actor = actor
        self.model = actor.model
        # self.direction = actor.direction

    @property
    def layer(self) -> PatchModule:
        """The current layer of the operating actor."""
        return self.actor.layer

    def _operating_layer(self, layer: PatchModule) -> bool:
        """
        This method is used to check if the input layer is consistent with the actor's layer.
        """
        if self.layer is None and layer is None:
            raise ABSESpyError("No operating layer is specified.")
        if self.layer is layer or self.layer is None:
            return layer
        if layer is None:
            return self.layer
        raise ABSESpyError(
            "The input layer is not consistent with the actor's layer."
        )

    def to(
        self, pos: PatchCell | Coordinate, layer: Optional[PatchModule] = None
    ) -> None:
        """
        This method is used to move the actor to a specific location.
        """
        # 检查这个位置的类型，返回图层和位置
        layer, pos = _get_layer_and_position(pos, layer=layer)
        # 检查操作图层
        operating_layer = self._operating_layer(layer=layer)
        move_agent_to(self.actor, layer=operating_layer, pos=pos)

    def off(self) -> None:
        """
        This method is used to remove.
        """
        if self.actor.on_earth:
            self.actor.at.agents.remove(self.actor)
        del self.actor.at

    def by(self, direction: str, distance: int = 1) -> bool:
        """
        This method is used to move the actor by a specific distance.
        """
        if not self.actor.on_earth:
            raise ABSESpyError(
                "The actor is not located on a cell, thus cannot move."
            )
        old_row, old_col = self.actor.at.indices
        if direction == "left":
            new_indices = (old_row, old_col - distance)
        elif direction == "right":
            new_indices = (old_row, old_col + distance)
        elif direction == "up":
            new_indices = (old_row - distance, old_col)
        elif direction == "down":
            new_indices = (old_row + distance, old_col)
        elif direction in {"up left", "left up"}:
            new_indices = (old_row - distance, old_col - distance)
        elif direction in {"up right", "right up"}:
            new_indices = (old_row - distance, old_col + distance)
        elif direction in {"down left", "left down"}:
            new_indices = (old_row + distance, old_col - distance)
        elif direction in {"down right", "right down"}:
            new_indices = (old_row + distance, old_col + distance)
        cell = self.layer.array_cells[new_indices[0]][new_indices[1]]
        self.actor.move.to(cell)

    def random(self, prob: Optional[str] = None, **kwargs):
        """
        This method is used to move the actor to a random location.
        """
        cells = self.actor.at.get_neighboring_cells(**kwargs)
        self.actor.move.to(cells.random.choice(prob=prob))
