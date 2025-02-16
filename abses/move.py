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
from mesa_geo import RasterLayer

from abses._bases.errors import ABSESpyError
from abses.actor import alive_required
from abses.cells import PatchCell

if TYPE_CHECKING:
    from abses.actor import Actor
    from abses.nature import PatchModule

MovingDirection: TypeAlias = Literal[
    "left", "right", "up", "down", "up left", "up right", "down left", "down right"
]


def _get_layer_and_position(
    pos: Coordinate | PatchCell,
    layer: Optional[PatchModule] = None,
    indices: bool = False,
) -> Tuple[Optional[PatchModule], Coordinate]:
    if isinstance(pos, PatchCell):
        if layer is not None and layer is not pos.layer:
            raise ABSESpyError(
                "The input layer is not consistent with the cell's layer."
            )
        return pos.layer, pos.indices if indices else pos.pos
    if isinstance(pos, tuple) and len(pos) == 2:
        return layer, pos
    raise TypeError(f"Invalid position type {pos}.")


def _put_agent_on_cell(agent: Actor, cell: PatchCell) -> None:
    """
    This function is used to put an agent on a cell.
    """
    if not isinstance(cell, PatchCell):
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
    cell.agents.add(agent)
    agent.at = cell


class _Movements:
    """A class that handles actor movement in the simulation.

    This class provides methods for moving actors between cells in the simulation grid.
    It handles basic movement operations like moving to specific coordinates, moving
    in directions, and random movement.

    Attributes:
        actor: The actor instance this movement handler belongs to.
        model: The model instance this movement handler operates in.
        seed: Unique identifier for the actor, used for random number generation.
    """

    def __init__(self, actor: Actor) -> None:
        self.actor = actor
        self.model = actor.model
        self.seed = actor.unique_id

    def __call__(
        self, how: MovingDirection | Literal["random"] = "random", **kwargs: Any
    ) -> None:
        if how == "random":
            self.random(**kwargs)
        else:
            self.by(how, **kwargs)

    @property
    def layer(self) -> Optional[PatchModule]:
        """The current layer of the operating actor."""
        return self.actor.layer

    def _layer_is_consistent(self, layer: PatchModule) -> None:
        if self.layer is None:
            return
        if self.layer is not layer:
            raise ABSESpyError(f"Layer {layer} inconsistent with the {self.layer}.")

    def _operating_layer(self, layer: Optional[PatchModule]) -> PatchModule:
        """
        This method is used to check if the input layer is consistent with the actor's layer.
        """
        if isinstance(layer, RasterLayer):
            if self.layer is None:
                return layer
            self._layer_is_consistent(layer)
            return self.layer
        if layer is None:
            if self.layer is None:
                raise ABSESpyError("No operating layer is specified.")
            return self.layer
        raise TypeError(f"Invalid layer type {layer}.")

    def to(
        self,
        to: PatchCell | Coordinate | Literal["random"] | None = None,
        layer: Optional[PatchModule] = None,
        indices: bool = False,
    ) -> None:
        """
        Move the actor to a specific location.

        Parameters:
            to:
                The position to move to.
                If position is a Coordinate -a tuple of (row, col),
                it will be moved to the same layer.
                If pos is None, the actor will be removed from the world.
            indices:
                The indices to move to.
            layer:
                The layer where the actor is located.
                If layer is None, the actor will be moved to the same layer as the actor's current layer.
            indices:
                Whether the position is indices.
                If indices is True, the position is indices.
                If indices is False, the position is position.

        Raises:
            ABSESpyError:
                If the input layer is not consistent with the actor's layer.
                If the position is out of bounds.
                Or, if the pos is coordinate without layer.
        """
        if isinstance(to, PatchCell):
            self._layer_is_consistent(to.layer)
            _put_agent_on_cell(self.actor, to)
            return
        if layer is None and self.layer is None:
            raise ABSESpyError("No operating layer is specified.")
        layer = self._operating_layer(layer=layer)
        if to == "random":
            cell = cast(PatchCell, layer.cells_lst.random.choice())
            _put_agent_on_cell(self.actor, cell)
            return
        if isinstance(to, tuple) and len(to) == 2:
            x, y = to
            if indices:
                cell = layer.array_cells[x, y]
            else:
                cell = layer.cells[x][y]
            _put_agent_on_cell(self.actor, cell)
            return
        # 检查这个位置的类型，返回图层和位置
        raise TypeError(f"Invalid position type {to}.")

    def off(self) -> None:
        """Remove the actor from the world.

        Raises:
            ABSESpyError:
                If the actor is not located on a cell, thus cannot move.
        """
        if self.actor.at is None:
            return
        if hasattr(self.actor.at, "agents"):
            self.actor.at.agents.remove(self.actor)
        del self.actor.at

    @alive_required
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
            raise ABSESpyError("The actor is not located on a cell, thus cannot move.")
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
        cell = self.layer.array_cells[new_indices[0], new_indices[1]]
        self.actor.move.to(cell, indices=True)

    @alive_required
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
