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

from typing import TYPE_CHECKING, Any, Literal, Optional, Tuple, cast

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

from mesa.space import Coordinate
from mesa_geo.raster_layers import RasterBase

from abses.errors import ABSESpyError
from abses.links import _LinkNodeCell

if TYPE_CHECKING:
    from abses.actor import Actor
    from abses.cells import PatchCell
    from abses.nature import PatchModule

MovingDirection: TypeAlias = Literal[
    "left",
    "right",
    "up",
    "down",
    "up left",
    "up right",
    "down left",
    "down right",
]


def _get_layer_and_position(
    pos: Coordinate | PatchCell, layer: Optional[PatchModule] = None
) -> Tuple[Optional[PatchModule], Coordinate]:
    if isinstance(cast("PatchCell", pos), _LinkNodeCell):
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
    if not isinstance(cell, _LinkNodeCell):
        raise TypeError(
            f"Agent must be put on a `abses.PatchCell`, instead of {type(cell)}"
        )
    # leave the old cell.
    if agent.on_earth:
        agent.move.off()
    # before moving to the new cell, agent may do something
    keep_moving = agent.moving(cell=cell)
    if keep_moving is False:
        return
    # put the agent on the new cell after check.
    cell.agents.add(agent, register=True)
    agent.at = cell
    # self.geometry = Point(cell.layer.transform * cell.indices)


def move_agent_to(
    agent: Actor,
    layer: PatchModule,
    pos: Coordinate | _LinkNodeCell,
) -> None:
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
    if not isinstance(layer, RasterBase):
        raise TypeError(f"{layer} is not valid 'PatchModule'.")
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
    def layer(self) -> Optional[PatchModule]:
        """The current layer of the operating actor."""
        return self.actor.layer

    def _operating_layer(
        self, layer: Optional[PatchModule]
    ) -> Optional[PatchModule]:
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
        self,
        pos: PatchCell | Coordinate | Literal["random"],
        layer: Optional[PatchModule] = None,
    ) -> None:
        """
        Move the actor to a specific location.

        Parameters:
            pos:
                The position to move to.
                If position is a Coordinate -a tuple of (row, col),
                it will be moved to the same layer.
                If pos
            layer:
                The layer where the actor is located.

        Raises:
            ABSESpyError:
                If the input layer is not consistent with the actor's layer.
                If the position is out of bounds.
                Or, if the pos is coordinate without layer.
        """
        if isinstance(pos, str) and pos == "random":
            # 随机分配一个该图层的位置
            operating_layer = self._operating_layer(layer=layer)
            assert operating_layer is not None
            pos = operating_layer.select().random.choice()
        else:
            # 检查这个位置的类型，返回图层和位置
            layer, pos = _get_layer_and_position(pos, layer=layer)
            operating_layer = self._operating_layer(layer=layer)
            assert operating_layer is not None
        move_agent_to(self.actor, layer=operating_layer, pos=pos)

    def off(self) -> None:
        """Remove the actor from the world."""
        if self.actor.at is None:
            raise ABSESpyError("The actor is not located on a cell.")
        if self.actor.on_earth:
            container = self.actor.at.agents
            if container is None:
                raise ABSESpyError("The actor is not located on a cell.")
            container.remove(self.actor)
        del self.actor.at

    def by(self, direction: MovingDirection, distance: int = 1) -> None:
        """Move the actor by a specific distance.

        Parameters:
            direction:
                The direction to move.
                It should be a direction string such as:
                "left", "right", "up", "down", "up left", "up right", "down left", "down right".
            distance:
                The distance to move toward the direction.

        Raises:
            ABSESpyError:
                If the actor is not located on a cell, thus cannot move.
            ValueError:
                If the direction is invalid.
        """
        if (self.actor.at is None) or (self.layer is None):
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
        else:
            raise ValueError(f"Invalid direction {direction}.")
        cell = self.layer.array_cells[new_indices[0]][new_indices[1]]
        self.actor.move.to(cell)

    def random(self, prob: Optional[str] = None, **kwargs: Any) -> None:
        """Move the actor to a random location nearby.

        Parameters:
            prob:
                The probability to select a cell.
            kwargs:
                Passing keyword args to `PatchCell.neighboring`,
                used to select neighboring cells.
        """
        if self.actor.at is None:
            raise ABSESpyError("The actor is not located on a cell.")
        cells = self.actor.at.neighboring(**kwargs)
        self.actor.move.to(cells.random.choice(prob=prob))
