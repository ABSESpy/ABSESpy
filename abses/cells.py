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

from numbers import Number
from typing import TYPE_CHECKING, Any, Callable, Optional, Tuple, Union

import mesa_geo as mg

from abses import ActorsList
from abses.container import _CellAgentsContainer
from abses.errors import ABSESpyError
from abses.links import TargetName, _LinkNode

if TYPE_CHECKING:
    from abses.main import H, MainModel, N
    from abses.nature import PatchModule

try:
    from typing import Self, TypeAlias
except ImportError:
    from typing_extensions import Self, TypeAlias

Pos: TypeAlias = Tuple[int, int]


def raster_attribute(func: Callable[..., Union[Number, str]]) -> property:
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
    setattr(func, "is_decorated", True)
    return property(func)


class PatchCell(mg.Cell, _LinkNode):
    """A patch cell of a `RasterLayer`.
    Subclassing this class to create a custom cell.
    When class attribute `max_agents` is assigned,
    the `agents` property will be limited to the number of agents.

    Attributes:
        agents:
            The agents located at here.
        layer:
            The `RasterLayer` where this `PatchCell` belongs.
    """

    max_agents: Optional[int] = None

    def __init__(
        self, pos: Optional[Pos] = None, indices: Optional[Pos] = None
    ):
        mg.Cell.__init__(self, pos, indices)
        _LinkNode.__init__(self)
        self._agents: Optional[_CellAgentsContainer] = None
        self._layer: Optional[PatchModule] = None

    def __repr__(self) -> str:
        return f"<Cell at {self.layer}[{self.pos}]>"

    @classmethod
    def __attribute_properties__(cls) -> set[str]:
        """Properties that should be found in the `RasterLayer`.

        Users should decorate a property attribute when subclassing `PatchCell` to make it accessible in the `RasterLayer`.
        """
        return {
            name
            for name, method in cls.__dict__.items()
            if isinstance(method, property)
            and getattr(method.fget, "is_decorated", False)
        }

    @property
    def layer(self) -> PatchModule:
        """`RasterLayer` where this `PatchCell` belongs."""
        if self._layer is None:
            raise ABSESpyError(
                "PatchCell must belong to a layer."
                f"However, {self} has no layer."
                "Did you create this cell in the correct way?"
            )
        return self._layer

    @layer.setter
    def layer(self, layer: PatchModule) -> None:
        if not isinstance(layer, mg.RasterLayer):
            raise TypeError(f"{type(layer)} is not valid layer.")
        if self._layer is not None:
            raise ABSESpyError("PatchCell can only belong to one layer.")
        # set layer property
        self._layer = layer
        # set layer's model as the model
        self.model: MainModel[Any, Any] = layer.model
        # set agents container
        self._agents = _CellAgentsContainer(
            layer.model, cell=self, max_len=getattr(self, "max_agents", None)
        )

    @property
    def agents(self) -> Optional[_CellAgentsContainer]:
        """The agents located at here."""
        return self._agents

    def _default_redirection(
        self, target: Optional[TargetName]
    ) -> _CellAgentsContainer | None:
        return self if target == "cell" else self.agents

    def get(self, attr: str, target: Optional[TargetName] = None) -> Any:
        """Gets the value of an attribute or registered property.
        Automatically update the value if it is the dynamic variable of the layer.

        Parameters:
            attr:
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
        return super().get(attr=attr, target=target)

    def neighboring(
        self,
        moore: bool = False,
        radius: int = 1,
        include_center: bool = False,
        annular: bool = False,
    ) -> ActorsList[Self]:
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
