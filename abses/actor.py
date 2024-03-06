#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/
from __future__ import annotations

from functools import cached_property, wraps
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    Optional,
    Self,
    TypeAlias,
    Union,
)

import mesa_geo as mg

from abses.decision import DecisionFactory
from abses.errors import ABSESpyError
from abses.links import LinkNode
from abses.move import _Movements
from abses.objects import _BaseObj
from abses.sequences import ActorsList
from abses.tools.func import make_list

# A class that is used to store the position of the agent.


if TYPE_CHECKING:
    from abses.human import LinkContainer
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
        self._cell: PatchCell = None
        self._container: LinkContainer = model.human
        self._decisions: DecisionFactory = self._setup_decisions()

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
    def on_earth(self) -> bool:
        """Whether agent stands on a cell"""
        return bool(self._cell)

    @property
    def here(self) -> ActorsList:
        """Other agents on the same cell as the agent."""
        return self._cell.agents

    @property
    def at(self) -> PatchCell | None:
        """Get the cell where the agent is located."""
        return self._cell if self._cell is not None else None

    @at.setter
    def at(self, cell: PatchCell) -> None:
        """Set the cell where the actor is located."""
        if not isinstance(cell, mg.Cell):
            raise TypeError(f"{cell} is not a cell.")
        if self not in cell.agents:
            raise ABSESpyError(
                "Cannot set location directly because the actor is not added to the cell."
            )
        self._cell = cell

    @at.deleter
    def at(self) -> None:
        """Remove the agent from the located cell."""
        if self.on_earth and self in self.at.agents:
            raise ABSESpyError(
                "Cannot remove location directly because the actor is still on earth."
            )
        self._cell = None

    @cached_property
    def move(self) -> _Movements:
        """Manipulating agent's location."""
        return _Movements(self)

    def get(
        self,
        attr: str,
        aggfunc: Optional[Callable] = None,
        target: Optional[Self | PatchCell] = None,
    ) -> Any:
        """Gets attribute value from target.
        attr:
            The name of the attribute to get.
        aggfunc:
            The function to aggregate the result.
        target:
            The target to get the attribute from. If None, the agent itself is the target.
            1. If the target is an agent, get the attribute from the agent.
            2. If the target is a cell, get the attribute from the cell.
        """
        if target is None:
            target = self
        target.get(attr, aggfunc=aggfunc)
        raise AttributeError(f"{attr} not found in {target}")

    def set(self, attr: str, value: Any) -> None:
        """Sets the value of an attribute."""
        setattr(self, attr, value)

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
        self.remove_me_from_others()
        if self.on_earth:
            self.move.off()
        del self

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

    def linked(self, link_name: str) -> ActorsList:
        """Get all other actors linked to this actor.

        Parameters:
            link:
                The link to search for.

        Returns:
            A list of all actors linked to this actor.
        """
        return ActorsList(self.model, super().linked(link_name))
