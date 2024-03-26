#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
In `ABSESpy`, agents are also known as 'Actors'.

在 abses 中，主体也叫做 Actor（行动者）。
"""

from __future__ import annotations

from functools import cached_property, wraps
from typing import TYPE_CHECKING, Any, Callable, Iterable, Optional, Union

try:
    from typing import Self, TypeAlias
except ImportError:
    from typing_extensions import TypeAlias, Self

import mesa_geo as mg

from abses.decision import _DecisionFactory
from abses.errors import ABSESpyError
from abses.links import _LinkNode, _LinkProxy
from abses.move import _Movements
from abses.objects import _BaseObj
from abses.tools.func import make_list

if TYPE_CHECKING:
    from abses.human import LinkContainer
    from abses.main import MainModel
    from abses.nature import PatchCell
    from abses.sequences import ActorsList


Selection: TypeAlias = Union[str, Iterable[bool]]
Trigger: TypeAlias = Union[Callable, str]
Targets: TypeAlias = Union["ActorsList", "Self", "PatchCell", "str"]
Breeds: TypeAlias = Optional[Union[str, Iterable[str]]]

TARGET_KEYWORDS = {
    "at": "at",
    "world": "at",
    "nature": "at",
    "me": "self",
    "actor": "self",
    "agent": "self",
}


def perception_result(name, result, nodata: Any = 0.0) -> Any:
    """clean the result of a perception.

    Parameters:
        name:
            The name of the perception.
        result:
            The result of the perception.
        nodata:
            The value to return if the result is None.
    """
    if hasattr(result, "__iter__"):
        raise ValueError(
            f"Perception result of '{name}' got type {type(result)} as return."
        )
    return nodata if result is None else result


def perception(
    decorated_func: Optional[Callable] = None, *, nodata: Optional[Any] = None
) -> Callable:
    """Change the decorated function into a perception attribute.

    Parameters:
        decorated_func:
            The decorated function.
        nodata:
            The value to return if the result is None.

    Returns:
        The decorated perception attribute or a decorator.
    """

    def decorator(func) -> Callable:
        @wraps(func)
        def wrapper(self: Actor, *args, **kwargs):
            result = func(self, *args, **kwargs)
            return perception_result(func.__name__, result, nodata=nodata)

        return wrapper

    # 检查是否有参数传递给装饰器，若没有则返回装饰器本身
    return decorator(decorated_func) if decorated_func else decorator


class Actor(mg.GeoAgent, _BaseObj, _LinkNode):
    """
    An actor in a social-ecological system (or "Agent" in an agent-based model.)

    Attributes:
        breed:
            The breed of this actor (by default, class name).
        layer:
            The layer where the actor is located.
        indices:
            The indices of the cell where the actor is located.
        pos:
            The position of the cell where the actor is located.
        on_earth:
            Whether the actor is standing on a cell.
        at:
            The cell where the actor is located.
        link:
            The link manipulating proxy.
        move:
            The movement manipulating proxy.

    Methods:
        get:
            Gets the value of an attribute from the actor or its cell.
        set:
            Sets the value of an attribute on the actor or its cell.
        die:
            Kills the actor.
    """

    # when checking the rules
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
        _LinkNode.__init__(self)
        self._cell: PatchCell = None
        self._decisions: _DecisionFactory = self._setup_decisions()
        self._setup()

    def __repr__(self) -> str:
        return f"<{self.breed} [{self.unique_id}]>"

    def _setup_decisions(self) -> _DecisionFactory:
        """Decisions that this actor makes."""
        decisions = make_list(getattr(self, "__decisions__", None))
        return _DecisionFactory(self, decisions)

    @property
    def decisions(self) -> _DecisionFactory:
        """The decisions that this actor makes."""
        return self._decisions

    # alias of decisions
    d = decisions

    @property
    def layer(self) -> mg.RasterLayer | None:
        """Get the layer where the actor is located."""
        return None if self._cell is None else self._cell.layer

    @property
    def on_earth(self) -> bool:
        """Whether agent stands on a cell."""
        return bool(self._cell)

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
        self.pos = cell.pos

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
        """A proxy for manipulating actor's location.

        1. `move.to()`: moves the actor to another cell.
        2. `move.off()`: removes the actor from the current layer.
        3. `move.by()`: moves the actor by a distance.
        4. `move.random()`: moves the actor to a random cell.
        """
        return _Movements(self)

    @cached_property
    def link(self) -> _LinkProxy:
        """A proxy which can be used to manipulate the links:

        1. `link.to()`: creates a new link from this actor to another.
        2. `link.by()`: creates a new link from another to this actor.
        3. `link.get()`: gets the links of this actor.
        4. `link.has()`: checks if there is a link between this actor and another.
        5. `link.unlink()`: removes a link between this actor and another.
        6. `link.clean()`: removes all links of this actor.
        """
        return _LinkProxy(self, self.model)

    def _get_correct_target(self, target: Targets, attr: str) -> Targets:
        """Which targets should be used when getting or setting."""
        # If the target is not None, get the target from dict.
        if target is not None:
            if isinstance(target, str):
                target = TARGET_KEYWORDS.get(target, target)
                target = {"self": self, "at": self.at}[target]
            return target
        # If the attribute is in the agent, the agent is the target.
        if hasattr(self, attr):
            return self
        # If the attribute is in the cell, the cell is the target.
        if self.on_earth and hasattr(self.at, attr):
            return self._cell
        # If the attribute is not found, raise an error.
        warn = "Set a new attribute outside '__init__' is not allowed."
        raise AttributeError(f"Attribute '{attr}' not found in {self}. {warn}")

    def get(
        self,
        attr: str,
        target: Optional[Self | PatchCell] = None,
    ) -> Any:
        """Gets attribute value from target.

        Parameters:
            attr:
                The name of the attribute to get.
            target:
                The target to get the attribute from.
                If None, the agent itself is the target.
                If the target is an agent, get the attribute from the agent.
                If the target is a cell, get the attribute from the cell.

        Returns:
            The value of the attribute.
        """
        target = self._get_correct_target(target, attr=attr)
        return getattr(self, attr) if target is self else target.get(attr)

    def set(self, attr: str, value: Any, target: Targets) -> None:
        """Sets the value of an attribute.

        Parameters:
            attr:
                The name of the attribute to set.
            value:
                The value to set the attribute to.
            target:
                The target to set the attribute on. If None, the agent itself is the target.
                1. If the target is an agent, set the attribute on the agent.
                2. If the target is a cell, set the attribute on the cell.

        Raises:
            TypeError:
                If the attribute is not a string.
            ABSESpyError:
                If the attribute is protected.
        """
        # If the attribute is not a string, raise an error.
        if not isinstance(attr, str):
            raise TypeError("The attribute must be a string.")
        # If the attribute is protected, raise an error
        if attr.startswith("_"):
            raise ABSESpyError(f"Attribute '{attr}' is protected.")
        # Set the attribute on the target.
        target = self._get_correct_target(target=target, attr=attr)
        setattr(target, attr, value)

    def die(self) -> None:
        """Kills the agent (self)"""
        self.link.clean()  # 从链接中移除
        if self.on_earth:  # 如果在地上，那么从地块上移除
            self.move.off()
        self.model.agents.remove(self)  # 从总模型里移除
        del self

    def _setup(self) -> None:
        """Setup the actor."""
        self.setup()

    def setup(self) -> None:
        """Overwrite this method.
        It should be called when the actor is initialized.
        """

    def moving(self, cell: PatchCell) -> None:
        """Overwrite this method.
        It should be called when the actor is moved.
        """
