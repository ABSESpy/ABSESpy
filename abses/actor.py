#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/
from __future__ import annotations

import logging
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    TypeAlias,
    Union,
)

import mesa_geo as mg
from mesa.space import Coordinate
from omegaconf import DictConfig
from shapely import Point

from abses.links import LinkNode
from abses.objects import _BaseObj
from abses.sequences import ActorsList

# A class that is used to store the position of the agent.


if TYPE_CHECKING:
    from abses.links import LinkContainer
    from abses.main import MainModel
    from abses.nature import PatchCell


Selection: TypeAlias = Union[str, Iterable[bool]]
Trigger: TypeAlias = Union[Callable, str]

logger = logging.getLogger("__name__")


def parsing_string_selection(selection: str) -> Dict[str, Any]:
    """
    Parses a string selection expression and returns a dictionary of key-value pairs.

    Parameters
    ----------
    selection: str
       String specifying which breeds to select.

    Returns
    -------
    selection_dict: dict
         Dictionary
    """
    selection_dict = {}
    if "==" not in selection:
        return {"breed": selection}
    expressions = selection.split(",")
    for exp in expressions:
        left, right = tuple(exp.split("=="))
        selection_dict[left.strip(" ")] = right.strip(" ")
    return selection_dict


def perception(func) -> Callable:
    """感知世界"""

    @property
    def wrapper(self: Actor, *args, **kwargs):
        """感知"""
        return func(self, *args, **kwargs)

    return wrapper


class Actor(mg.GeoAgent, _BaseObj, LinkNode):
    """
    An actor in a social-ecological system (or "Agent" in an agent-based model.)

    Attributes:
        _freq_levels:
            A dictionary that maps frequency levels to integer codes. The frequency levels are used to determine when rules should be checked.
            The available frequency levels are "now", "update", "move", and "any".
        _cell:
            The cell where the actor is located.
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
        self.container: LinkContainer = model.human

    def put_on(self, cell: PatchCell | None = None) -> None:
        """
        Place agent on a cell (same layer)

        Parameters
        ----------
        cell : PatchCell
            The cell where the agent is to be located.

        Raises
        ------
        IndexError
            If the agent is to be moved between different layers.
        TypeError
            If the agent is to be put on a non-PatchCell object.

        Returns
        -------
        None
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

    def put_on_layer(self, layer: mg.RasterLayer, pos: Tuple[int, int]):
        """
        Specifies a new cell for the agent to be located on.

        Parameters
        ----------
        layer : mg.RasterLayer
            The layer where the agent is to be located.
        pos : Tuple[int, int]
            The position of the cell where the agent is to be located.

        Raises
        ------
        TypeError

        Returns
        -------
        None
        """
        if not isinstance(layer, mg.RasterLayer):
            raise TypeError(f"{layer} is not mg.RasterLayer.")
        cell = layer.cells[pos[0]][pos[1]]
        self.put_on(cell=cell)

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

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name[0] != "_" and hasattr(self, "_rules"):
            self._check_rules(check_when="any")

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

    def _freq_level(self, level: str) -> int:
        code = self._freq_levels.get(level)
        if code is None:
            keys = tuple(self._freq_levels.keys())
            raise KeyError(f"freq level {level} is not available in {keys}")
        return code

    def _check_rules(self, check_when: str) -> List[str]:
        triggered_rules = []
        for name in list(self._rules.keys()):
            rule = self._rules[name]
            parameters = rule.get("params", {})
            if rule.frequency < self._freq_level(check_when):
                continue
            if self.selecting(rule.when) is True:
                triggered_rules.append(name)
                # check if is a disposable rule
                if rule.disposable is True:
                    # self.logger.debug(
                    #     f"Rule '{name}' applied on '{self}' in {self.time}."
                    # )
                    del self._rules[name]
                getattr(self, rule.then)(**parameters)
        # delete disposable rules
        return triggered_rules

    def selecting(self, selection: Union[str, Dict[str, Any]]) -> bool:
        """
        Either select the agent according to specified criteria

        Parameters
        ----------
        selection: Union[str, Dict[str, Any]]
            Either a string or a dictionary of key-value pairs that represent agent attributes to be checked against.

        Returns
        -------
        bool
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

    def rule(
        self,
        when: Selection,
        then: Trigger,
        name: Optional[str] = None,
        frequency: str = "any",
        disposable: bool = False,
        check_now: Optional[bool] = True,
        **kwargs,
    ):
        """
        Set up a rule that is activated at time period `when` and triggers a function `then`.\

        Parameters
        ----------
        when: Union[str, Iterable[bool]]
            Condition to be checked
        then: Union[callable, str]
            Trigger to be activated
        name: Optional[str]
            Name for the set of rules
        frequency: str
            Any of the following: 'now', 'update', 'move', 'any'
        disposanle: bool
            Is this set of rules disposable
        check_now: Optional[bool]
            Whether to check the rules now
        **kwargs: Any
            Addional keyword arguments to be passed to the trigger function

        Returns
        -------
        Optional[List]
            A list of triggered rules
        """
        if name is None:
            name = f"rule ({len(self._rules) + 1})"
        self._rules[name] = DictConfig(
            {
                "when": when,
                "then": then,
                "params": kwargs,
                "disposable": disposable,
                "frequency": self._freq_level(frequency),
            }
        )
        if check_now is True:
            self._check_rules("now")

    def die(self) -> None:
        """
        Kills the agent (self)

        Returns
        -------
        None
        """
        self.model.agents.remove(self)
        for link in self.links:
            self.container.get_graph(link).remove_node(self)
        if self.on_earth:
            self._cell.remove(self)
            del self

    def move_to(self, position: Optional[Tuple[int, int]]) -> bool:
        """
        Move agent to a new position

        Parameters
        ----------
        position : Optional[Tuple[int, int]]
            The new position to move to.

        Raises
        ------
        ValueError
            If the position

        """
        if not self.layer:
            raise ValueError("Layer is not set.")
        self.layer.move_agent(self, position)

    def loc(self, attribute: str) -> Any:
        """
        Get attribute data for the cell where the actor is located.

        Parameters
        ----------
        attribute : str
            The name of the attribute to get.

        Raises
        ------
        AttributeError
            If the attribute is not found in the cell.

        Returns
        -------
        Any
        """
        return self._cell.get_attr(attribute)

    def alter_nature(self, attr: str, value: Any) -> None:
        """
        Alter the nature of the parameters of the cell where the actor is located.

        Parameters
        ----------
        attr : str
            The name of the parameter to change.

        value : Any
            The new value to assign to the parameter.

        Raises
        ------
        AttributeError
            If the attribute is not found in the cell.

        Returns
        -------
        None
        """
        if attr not in self._cell.attributes:
            raise AttributeError(f"Attribute {attr} not found.")
        setattr(self._cell, attr, value)

    def linked(self, link: str) -> ActorsList:
        """
        Get all other actors linked to this actor.

        Parameters
        ----------
        link : str
            The link to search for.

        Returns
        -------
        ActorsList
            A list of all actors linked to this actor.
        """
        return ActorsList(self.model, super().linked(link))
