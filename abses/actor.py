#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/
from __future__ import annotations

from functools import wraps
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    Optional,
    Tuple,
    TypeAlias,
    Union,
)

import mesa_geo as mg
from mesa.space import Coordinate
from shapely import Point

from abses.decision import DecisionFactory
from abses.errors import ABSESpyError
from abses.links import LinkNode
from abses.objects import _BaseObj
from abses.sequences import ActorsList
from abses.tools.func import make_list

# A class that is used to store the position of the agent.


if TYPE_CHECKING:
    from abses.main import MainModel
    from abses.nature import PatchCell


Selection: TypeAlias = Union[str, Iterable[bool]]
Trigger: TypeAlias = Union[Callable, str]


def parsing_string_selection(selection: str) -> Dict[str, Any]:
    """Parses a string selection expression and returns a dictionary of key-value pairs.

    Parameters:
        selection:
            String specifying which breeds to select.

    Returns:
        selection_dict:
            Parsed output as Dictionary
    """
    selection_dict = {}
    if "==" not in selection:
        return {"breed": selection}
    expressions = selection.split(",")
    for exp in expressions:
        left, right = tuple(exp.split("=="))
        selection_dict[left.strip(" ")] = right.strip(" ")
    return selection_dict


def perception_result(name, result, nodata: Any = 0.0) -> Any:
    """clean the result of a perception."""
    if hasattr(result, "__iter__"):
        # raise ABSESpyError('No')
        raise ValueError(
            f"Perception result of '{name}' got type {type(result)} as return."
        )
    return nodata if result is None else result


def perception(
    decorated_func: Callable | None = None, *, nodata: Any | None = None
) -> Callable:
    """Change the decorated function into a perception attribute."""

    def decorator(func) -> Callable:
        @wraps(func)
        def wrapper(self: Actor, *args, **kwargs):
            result = func(self, *args, **kwargs)
            return perception_result(func.__name__, result, nodata=nodata)

        return wrapper

    # 检查是否有参数传递给装饰器，若没有则返回装饰器本身
    return decorator(decorated_func) if decorated_func else decorator


class Actor(mg.GeoAgent, _BaseObj, LinkNode):
    """
    An actor in a social-ecological system (or "Agent" in an agent-based model.)

    Attributes:
        container:
            The container that the actor belongs to.
        layer:
            The layer where the actor is located.
        indices:
            The indices of the cell where the actor is located.
        pos:
            The position of the cell where the actor is located.
        population:
            A list of actors of the same breed as the actor.
        on_earth:
            Whether the actor is standing on a cell.
        here:
            A list of actors that are on the same cell as the actor.

    Methods:
        put_on(self, cell: PatchCell | None = None) -> None
            Places the actor on a cell.
        put_on_layer(self, layer: mg.RasterLayer, pos: Tuple[int, int])
            Specifies a new cell for the actor to be located on.
        selecting(self, selection: Union[str, Dict[str, Any]]) -> bool
            Selects the actor according to specified criteria.
    """

    # when checking the rules
    _freq_levels: Dict[str, int] = {"now": 0, "update": 1, "move": 2, "any": 3}
    __decisions__ = None

    def __init__(
        self,
        model: MainModel,
        observer: bool = True,
        unique_id: Optional[int] = None,
        **kwargs,
    ) -> None:
        _BaseObj.__init__(self, model, observer=observer)
        if not unique_id:
            unique_id = self.model.next_id()
        crs = kwargs.pop("crs", model.nature.crs)
        geometry = kwargs.pop("geometry", None)
        mg.GeoAgent.__init__(
            self, unique_id, model=model, geometry=geometry, crs=crs
        )
        LinkNode.__init__(self)
        self._rules: Dict[str, Dict[str, Any]] = {}
        self._cell: PatchCell = None
        self.container = model.human
        self._decisions = self._setup_decisions()

    def _setup_decisions(self) -> DecisionFactory:
        """Decisions that this actor makes."""
        decisions = make_list(getattr(self, "__decisions__", None))
        return DecisionFactory(self, decisions)

    @property
    def decisions(self) -> DecisionFactory:
        """Decisions that this agent makes."""
        return self._decisions

    # alias of decisions
    d = decisions

    @property
    def layer(self) -> mg.RasterLayer:
        """Get the layer where the agent is located."""
        return None if self._cell is None else self._cell.layer

    @property
    def indices(self) -> Coordinate:
        """Coordinates in the form of (row, col) are used for indexing a matrix, with the origin at the top left corner and increasing downwards."""
        return self._cell.indices

    @property
    def pos(self) -> Coordinate:
        """Coordinates in the form of (x, y) indexed from the bottom left corner."""
        return self._cell.pos

    @pos.setter
    def pos(self, pos) -> None:
        if pos is not None:
            raise AttributeError(f"Set pos by {self.put_on_layer.__name__}")

    @property
    def population(self) -> ActorsList:
        """List of agents of the same breed"""
        return self.model.agents[self.breed]

    @property
    def on_earth(self) -> bool:
        """Whether agent stands on a cell"""
        return bool(self._cell)

    @property
    def here(self) -> ActorsList:
        """Other agents on the same cell as the agent."""
        return self._cell.agents

    def put_on(self, cell: PatchCell | None = None) -> None:
        """Place agent on a cell. If the agent is already located at a cell, it should be located to a cell with the same layer.

        Parameters:
            cell:
                The cell where the agent is to be located. If None (default), remove the subject from the current layer.

        Raises:
            IndexError:
                If the agent is to be moved between different layers.
            TypeError:
                If the agent is to be put on a non-PatchCell object.
        """
        if cell is None:
            # Remove agent
            self._cell = None
            return
        if self.layer and self.layer is not cell.layer:
            raise IndexError(
                f"Trying to move actor between different layers: from {self.layer} to {cell.layer}"
            )
        if not isinstance(cell, mg.Cell):
            raise TypeError(
                f"Actor must be put on a PatchCell, instead of {type(cell)}"
            )
        if self.on_earth:
            self._cell.remove(self)
            self._cell = None
        cell.add(self)
        self._cell = cell
        self.geometry = Point(cell.layer.transform * cell.indices)

    def put_on_layer(
        self, layer: mg.RasterLayer, pos: Tuple[int, int]
    ) -> None:
        """Specifies a new cell for the agent to be located on.

        Parameters:
            layer:
                The layer where the agent is to be located.
            pos:
                The position of the cell where the agent is to be located.

        Raises:
            TypeError:
                If the layer is not a valid RasterLayer type.
        """
        if not isinstance(layer, mg.RasterLayer):
            raise TypeError(f"{layer} is not mg.RasterLayer.")
        cell = layer.cells[pos[0]][pos[1]]
        self.put_on(cell=cell)

    def selecting(self, selection: Union[str, Dict[str, Any]]) -> bool:
        """Either select the agent according to specified criteria.

        Parameters:
            selection:
                Either a string or a dictionary of key-value pairs that represent agent attributes to be checked against.

        Returns:
            Whether the agent is selected or not
        """
        if isinstance(selection, str):
            selection = parsing_string_selection(selection)
        results = []
        for k, v in selection.items():
            attr = getattr(self, k, None)
            if attr is None:
                results.append(False)
            elif attr == v or str(attr) == v:
                results.append(True)
            else:
                results.append(False)
        return all(results)

    def die(self) -> None:
        """Kills the agent (self)"""
        self.model.agents.remove(self)
        for link in self.links:
            self.container.get_graph(link).remove_node(self)
        if self.on_earth:
            self._cell.remove(self)
            del self

    def move_to(self, position: Optional[Coordinate]) -> bool:
        """Move agent to a new position.

        Parameters:
            position:
                The new position to move to.

        Raises:
            ValueError:
                The main body is not on the same layer, please use the put_on method first.
        """
        if not self.layer:
            raise ValueError("Layer is not set.")
        self.layer.move_agent(self, position)

    def loc(self, attribute: str) -> Any:
        """Get attribute data for the cell where the actor is located.

        Parameters:
            attribute : str
                The name of the attribute to get.

        Raises:
            AttributeError:
                If the attribute is not found in the cell where this agent is located.
            ABSESpyError:
                The agent is not in the environment.
        """
        if self.on_earth:
            return self._cell.get_attr(attribute)
        raise ABSESpyError(
            f"You should locate this agent ({self}) to somewhere before get associated attribute."
        )

    def alter_nature(self, attr: str, value: Any) -> None:
        """Alter the nature of the parameters of the cell where the actor is located.

        Parameters:
            attr:
                The name of the parameter to change.
            value:
                The new value to assign to the parameter.

        Raises:
            AttributeError:
                If the attribute is not found in the cell.
        """
        if not hasattr(self._cell, attr):
            raise AttributeError(f"Attribute {attr} not found.")
        setattr(self._cell, attr, value)

    def linked(self, link: str) -> ActorsList:
        """Get all other actors linked to this actor.

        Parameters:
            link:
                The link to search for.

        Returns:
            A list of all actors linked to this actor.
        """
        return ActorsList(self.model, super().linked(link))
