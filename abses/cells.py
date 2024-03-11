#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
每一个世界里的斑块
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any

import mesa_geo as mg

from abses import ActorsList
from abses.container import _CellAgentsContainer
from abses.links import _LinkNode, _LinkProxy

if TYPE_CHECKING:
    from abses.main import MainModel
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


class PatchCell(mg.Cell, _LinkNode):
    """A patch cell of a `RasterLayer`.

    Attributes:
        agents:
            The agents located at here.
        layer:
            The `RasterLayer` where this `PatchCell` belongs.
    """

    def __init__(self, pos=None, indices=None):
        mg.Cell.__init__(self, pos, indices)
        _LinkNode.__init__(self)
        self._agents = None
        self._layer = None

    def __repr__(self) -> str:
        return f"<Cell at {self.layer}[{self.pos}]>"

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
        self._agents = _CellAgentsContainer(layer.model, cell=self)

    @property
    def agents(self) -> _CellAgentsContainer:
        """The agents located at here."""
        return self._agents

    @cached_property
    def link(self) -> _LinkProxy:
        """The link to the patch."""
        return _LinkProxy(node=self, model=self.layer.model)

    def get(self, attr: str) -> Any:
        """Gets the value of an attribute or registered property.
        Automatically update the value if it is the dynamic variable of the layer.

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
        if attr in self.layer.dynamic_variables:
            self.layer.dynamic_var(attr_name=attr)
        if not hasattr(self, attr):
            raise AttributeError(f"{attr} not exists in {self.layer}.")
        return getattr(self, attr)

    def neighboring(
        self,
        moore: bool = False,
        radius: int = 1,
        include_center: bool = False,
        annular: bool = False,
    ) -> ActorsList:
        """Get the grid around the patch."""
        cells = self.layer.get_neighboring_cells(
            self.pos, moore=moore, radius=radius, include_center=include_center
        )
        if annular:
            interiors = self.layer.get_neighboring_cells(
                self.pos, moore=moore, radius=radius - 1, include_center=False
            )
            return ActorsList(self.model, set(cells) - set(interiors))
        return ActorsList(self.model, cells)
