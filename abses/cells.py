#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

import mesa_geo as mg

from abses import Actor, ActorsList
from abses.errors import ABSESpyError
from abses.links import LinkNode
from abses.sequences import agg_agents_attr

if TYPE_CHECKING:
    from abses.nature import PatchModule


def raster_attribute(func):
    """Turn the method into a property that the patch can extract.
    Examples:
        ```
        class TestCell(Cell):
            @raster_attribute
            def test:
                return 1

        # Using this test cell to create a PatchModule.
        module = PatchModule.from_resolution(
            model=MainModel(),
            shape=(3, 3),
            cell_cls=TestCell,
        )

        # now, the attribute 'test' of TestCell can be accessible in the module, as spatial data (i.e., raster layer).

        >>> module.cell_properties
        >>> set('test')

        >>> array = module.get_raster('test')
        >>> np.array([
            [1, 1, 1],
            [1, 1, 1],
            [1, 1, 1],
        ])
        ```
    """
    func.is_decorated = True
    return property(func)


class PatchCell(mg.Cell, LinkNode):
    """A patch cell of a `RasterLayer`.

    Attributes:
        agents:
            The agents located at here.
        layer:
            The `RasterLayer` where this `PatchCell` belongs.
    """

    def __init__(self, pos=None, indices=None):
        mg.Cell.__init__(self, pos, indices)
        LinkNode.__init__(self)
        self._agents = {}
        self._layer = None

    def __repr__(self) -> str:
        return f"<PatchCell at {self.pos}>"

    @classmethod
    def __attribute_properties__(cls) -> set[str]:
        """Properties that should be found in the `RasterLayer`."""
        return {
            name
            for name, method in cls.__dict__.items()
            if isinstance(method, property)
            and getattr(method.fget, "is_decorated", False)
        }

    @property
    def layer(self) -> PatchModule:
        """`RasterLayer` where this `PatchCell` belongs."""
        return self._layer

    @layer.setter
    def layer(self, layer: PatchModule) -> None:
        if not isinstance(layer, mg.RasterLayer):
            raise TypeError(f"{type(layer)} is not valid layer.")
        self.container = layer.model.human
        self._layer = layer

    @classmethod
    @property
    def breed(cls) -> str:
        """Breed of this `PatchCell`"""
        return cls.__name__

    @property
    def agents(self) -> ActorsList[Actor]:
        """The agents located at here."""
        agents = []
        for _, agents_set in self._agents.items():
            agents.extend(agents_set)
        return ActorsList(self.model, agents)

    def has_agent(self, breed: Optional[str] = None) -> bool:
        """Whether the actor is standing at the current `PatchCell`.

        Parameters:
            breed:
                Specify the breed of agents to search. If None (by default), all breeds of agents are acceptable.

        Returns:
            bool:
                True if there is a qualified principal there, False otherwise.
        """
        return bool(self._agents) if breed is None else breed in self._agents

    def get_attr(self, attr_name: str) -> Any:
        """Gets the value of an attribute or registered property. Automatically update the value if it is the dynamic variable of the layer.

        Parameters:
            attr_name:
                The name of attribute to get.
                
        Returns:
            Any:
                The value of the attribute.
                
        Raises:
            AttributeError:
                Attribute value of the associated patch cell.
        """
        if attr_name in self.layer.dynamic_variables:
            self.layer.dynamic_var(attr_name=attr_name)
        if not hasattr(self, attr_name):
            raise AttributeError(f"{attr_name} not exists in {self.layer}.")
        return getattr(self, attr_name)

    def add(self, agent: Actor) -> None:
        """Adds an `Actor` to here.

        Parameters:
            agent:
                The `Actor` to be added.

        Raises:
            ABSESpyError:
                If the actor is already on earth (at another cell or another layer).
        """
        if agent.on_earth:
            raise ABSESpyError(f"{agent} is already on earth.")
        if not issubclass(agent.__class__, Actor):
            raise TypeError(
                f"The agent to be added should be an instance of 'Actor' or its subclass, not {type(agent)}."
            )
        if agent.breed not in self._agents:
            self._agents[agent.breed] = {agent}
        else:
            self._agents[agent.breed].add(agent)

    def remove(self, agent: Actor) -> None:
        """Removes an Actor here.

        Parameters:
            agent:
                The `Actor` to be removed.

        Raises:
            ABSESpyError:
                If the actor is not on this cell.
        """
        try:
            self._agents[agent.breed].remove(agent)
        except KeyError as err:
            raise ABSESpyError(f"{agent} is not located at {self}.") from err
        agent.put_on()
        if not self._agents[agent.breed]:
            del self._agents[agent.breed]

    def linked(self, link: str) -> ActorsList[Actor]:
        """Gets the body of the link to this patch.

        Parameters:
            link:
                The link type to search.

        Returns:
            An `ActorList` of `Actor` who has association with the patch.

        Raises:
            TypeError:
                The input link should be a string of link name.
            KeyError:
                The searched link is not available in the model.
        """
        if link is None:
            return self.agents
        elif not isinstance(link, str):
            raise TypeError(f"{type(link)} is not valid link name.")
        elif link not in self.links:
            raise KeyError(f"{link} not exists in {self}.")
        else:
            agents = ActorsList(self.model, super().linked(link=link))
        return agents

    def linked_attr(
        self,
        attr: str,
        link: Optional[str] = None,
        nodata: Any = None,
        how: str = "only",
    ) -> Any:
        """Gets the properties of the agent linked to the patch.

        Parameters:
            attr:
                The attribute name to retrieve.
            link:
                The link name to search associations.
            nodata:
                For the agents who don't have such an attribute, return a nodata as a placeholder.
            how:
                Search mode. #TODO

        Returns:
            Any type of retrieved data.
            
        Raises:
            KeyError:
                The searched link is not available in the model.
        """
        try:
            agents = self.linked(link=link)
        except KeyError:
            agents = ActorsList(self.model, [])
        if nodata is None or agents:
            return agg_agents_attr(agents=agents, attr=attr, how=how)
        return nodata

    def get_neighboring_cells(
        self,
        moore: bool = False,
        radius: int = 1,
        include_center: bool = False,
        annular: bool = False,
    ) -> ActorsList:
        """#TODO Get the grid around the patch."""
        cells = self.layer.get_neighboring_cells(
            self.pos, moore=moore, radius=radius, include_center=include_center
        )
        if annular:
            interiors = self.layer.get_neighboring_cells(
                self.pos, moore=moore, radius=radius - 1, include_center=False
            )
            return ActorsList(self.model, set(cells) - set(interiors))
        return ActorsList(self.model, cells)
