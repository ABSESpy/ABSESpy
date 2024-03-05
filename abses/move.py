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

from typing import TYPE_CHECKING, Optional

import mesa_geo as mg
from mesa.space import Coordinate

from abses.errors import ABSESpyError

if TYPE_CHECKING:
    from abses.actor import Actor
    from abses.cells import PatchCell
    from abses.nature import PatchModule


def _get_position(pos: Coordinate | PatchCell) -> Coordinate:
    if isinstance(pos, mg.Cell):
        return pos.pos
    if isinstance(pos, tuple) and len(pos) == 2:
        return pos
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
    pos = _get_position(pos)
    if not isinstance(layer, mg.RasterLayer):
        raise TypeError(f"{layer} is not mg.RasterLayer.")
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
    def layer(self) -> mg.RasterLayer:
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
        # 如果位置是一个单元格的坐标，那么检查这是在哪个图层进行操作
        if not isinstance(pos, mg.Cell):
            layer = self._operating_layer(layer)
        # 否则，检查这个单元格是不是在这个图层上
        elif layer is None or layer is pos.layer:
            layer = pos.layer
        # 如果图层不一致就报错
        else:
            raise ABSESpyError(
                f"Input layer {layer} is not the cell's layer {pos.layer}."
            )
        move_agent_to(self.actor, layer=layer, pos=pos)

    def off(self) -> None:
        """
        This method is used to remove.
        """
        del self.actor.at

    def by(self, direction: str = "random", distance: int = 1) -> bool:
        """
        This method is used to move the actor by a specific distance.
        """
