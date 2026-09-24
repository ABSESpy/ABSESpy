#!/usr/bin/env python3
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""ActorsList is a sequence of actors.
It's used to manipulate the actors quickly in batch.
"""

from __future__ import annotations

from collections.abc import Iterable
from numbers import Number
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Sized,
    Union,
    cast,
    overload,
)

import numpy as np
from mesa import Agent
from mesa.agent import AgentSet
from numpy.typing import NDArray

from abses.core.protocols import MainModelProtocol
from abses.core.types import A
from abses.utils.func import get_only_item
from abses.utils.random import ListRandom

if TYPE_CHECKING:
    from abses.core.types import HOW_TO_SELECT


class ActorsList(AgentSet, Generic[A]):
    """Extended agent set specifically designed for managing Actor collections.

    ActorsList extends Mesa's AgentSet with ABSESpy-specific functionality, providing
    enhanced batch operations on actor collections. It focuses on returning numpy
    arrays for efficient numerical operations and maintaining compatibility with
    other ABSESpy components.

    The class provides methods for filtering, grouping, updating attributes in batch,
    and performing vectorized operations on all actors in the collection. It serves
    as the primary return type for queries that retrieve multiple actors, such as
    container selections and breed-based lookups.

    Key features:
    - Numpy array returns for numerical operations
    - Batch attribute updates with validation
    - Grouping by breed or custom attributes
    - Integration with ABSESpy's random number generation
    - Type-safe operations through generic typing

    Attributes:
        _model: The ABSESpy model this list belongs to.
    """

    def __init__(
        self,
        model: MainModelProtocol,
        objs: Iterable[A] = (),
    ) -> None:
        """Initialize an ActorsList instance.

        Parameters:
            model: The ABSESpy model this list belongs to.
            objs: Iterable of actors to include in the list. Defaults to empty.
        """
        super().__init__(objs, random=model.random)
        self._model = model

    def __repr__(self) -> str:
        """Return a string representation of the ActorsList.

        The representation shows the count of actors grouped by breed.

        Returns:
            String in format "<ActorsList: (count1)breed1; (count2)breed2; ...>"
        """
        results = [f"({len(v)}){k}" for k, v in self.to_dict().items()]
        return f"<ActorsList: {'; '.join(results)}>"

    @overload
    def __getitem__(self, other: int) -> A: ...

    @overload
    def __getitem__(self, index: slice) -> ActorsList[A]: ...

    def __getitem__(self, index: Union[int, slice]) -> Union[A, ActorsList[A]]:
        """Get an actor or a slice of actors from the list.

        Parameters:
            index: Either an integer index or a slice object.

        Returns:
            A single actor if index is an integer, or an ActorsList if index is a slice.
        """
        results = super().__getitem__(index)
        return ActorsList(self._model, results) if isinstance(index, slice) else results

    def _is_same_length(self, length: Sized, rep_error: bool = False) -> bool:
        """Check if the length of input matches the number of actors.

        Parameters:
            length: An object with a __len__ method to compare.
            rep_error: If True, raises ValueError on mismatch. Defaults to False.

        Returns:
            True if lengths match.

        Raises:
            ValueError: If length doesn't have __len__ method or if lengths mismatch
                and rep_error is True.
        """
        if not hasattr(length, "__len__"):
            raise ValueError(f"{type(length)} object is not iterable.")
        if len(length) != len(self):
            if rep_error:
                raise ValueError(
                    f"Length of the input {len(length)} mismatch {len(self)} actors."
                )
        return True

    @property
    def linked_agents(self) -> ActorsList[A]:
        """Get the agents from the list.

        This property returns agents based on the list content:
        - If the list contains all cells, returns all agents located on those cells
        - If the list contains all actors, returns the cells where the actors are located
        - If the list is mixed, raises an error

        Returns:
            ActorsList containing the relevant agents (from cells) or cells (from actors).

        Raises:
            ABSESpyError: If the list contains both cells and actors (mixed).

        Example:
            ```python
            # From cells -> agents on those cells
            cells = model.nature.grid.cells_lst.select(lambda c: c.wealth > 100)
            agents_on_rich_cells = cells.linked_agents  # All agents on these cells

            # From actors -> cells where these actors are
            agents = model.agents.select(lambda a: a.wealth > 100)
            cells_where_agents_are = agents.linked_agents  # Cells where these agents are located
            ```
        """
        from abses.utils.errors import ABSESpyError

        if self.is_mixed:
            raise ABSESpyError(
                "Mixed list contains both cells and actors. Cannot get agents."
                " Please filter the list to contain only cells or only actors."
            )

        if self.is_cells:
            # Collect all agents from all cells
            all_agents = []
            for cell in self:
                all_agents.extend(cell.agents)  # _CellAgentsContainer is iterable
            return ActorsList(model=self._model, objs=all_agents)

        if self.is_actors:
            # Get cells where these actors are located
            cells = []
            for actor in self:
                if hasattr(actor, "at") and actor.at is not None:
                    cells.append(actor.at)
            return ActorsList(model=self._model, objs=cells)

        # Empty list or unknown type
        return ActorsList(model=self._model, objs=[])

    def to_dict(self) -> Dict[str, ActorsList[A]]:
        """Convert all actors to a dictionary grouped by breed.

        This method groups actors by their breed attribute and returns a dictionary
        where keys are breed names and values are ActorsList instances containing
        actors of that breed. This is useful for operations that need to process
        different actor types separately.

        Returns:
            Dictionary mapping breed names (str) to ActorsList containing actors
            of that breed.

        Example:
            ```python
            actors = model.agents.all()
            by_breed = actors.to_dict()
            farmers = by_breed['Farmer']  # All farmer actors
            ```
        """
        # 使用 groupby 按照 breed 属性分组
        grouped = self.groupby(by="breed")

        # 将分组结果转换为 ActorsList
        return {
            breed: ActorsList(self._model, agents)
            for breed, agents in grouped.groups.items()
        }

    def select(
        self,
        filter_func: Callable[[A], bool] | dict[str, Any] | str | None = None,
        at_most: int | float = float("inf"),
        inplace: bool = False,
        agent_type: Agent | None = None,
    ) -> ActorsList[A]:
        """Select actors from the list based on filter criteria.

        This method provides flexible filtering with support for callable functions,
        dictionaries of attribute-value pairs, or attribute names. It extends Mesa's
        select method to return ActorsList instances and support additional filter
        formats.

        Parameters:
            filter_func: Filter criteria. Can be:
                - A callable taking an agent and returning bool
                - A dictionary of {attribute: value} pairs for matching
                - A string attribute name (selects where attribute is truthy)
                - None to select all agents
            at_most: Maximum number of agents to select. Can be an integer or
                a fraction (0-1) of the current list size.
            inplace: If True, modifies current list; otherwise returns new list.
                Defaults to False.
            agent_type: Optional agent type to filter by.

        Returns:
            ActorsList containing the selected actors.

        Example:
            ```python
            # Select by callable
            rich_farmers = farmers.select(lambda f: f.wealth > 100)

            # Select by dict
            male_farmers = farmers.select({'gender': 'male'})

            # Select by attribute
            active = farmers.select('is_active')
            ```
        """
        if isinstance(filter_func, dict):
            key_value_pairs = filter_func

            def filter_func(agent: Agent) -> bool:
                return all(getattr(agent, k) == v for k, v in key_value_pairs.items())

        if isinstance(filter_func, str):
            attr_name = filter_func

            def filter_func(agent: Agent) -> bool:
                # Preserve the name before rebinding filter_func to this closure.
                return getattr(agent, attr_name)

        objects = super().select(filter_func, at_most, inplace, agent_type)
        return ActorsList(self._model, objects)

    def better(
        self, metric: str, than: Optional[Union[Number, A]] = None
    ) -> ActorsList[A]:
        """Select actors with a metric value better than a threshold.

        This method filters actors based on a numerical metric, selecting those
        with values greater than the specified threshold. If no threshold is
        provided, returns actors with the maximum metric value.

        Parameters:
            metric: Name of the attribute to compare.
            than: Threshold value. Can be a number, an actor (in which case
                the actor's metric value is used), or None (returns actors
                with maximum metric value).

        Returns:
            ActorsList containing actors with metric values greater than the threshold,
            or actors with the maximum metric value if than is None.

        Example:
            ```python
            # Select farmers wealthier than 100
            rich = farmers.better('wealth', than=100)

            # Select farmers wealthier than a specific farmer
            richer = farmers.better('wealth', than=specific_farmer)

            # Select the wealthiest farmer(s)
            wealthiest = farmers.better('wealth')  # than=None
            ```
        """
        if isinstance(than, Agent):
            than = getattr(than, metric)

        # If no threshold provided, select actors with maximum metric value
        if than is None:
            if len(self) == 0:
                return ActorsList(self._model, [])
            max_value = max(getattr(agent, metric) for agent in self)
            return self.select(lambda x: getattr(x, metric) == max_value)

        return self.select(lambda x: getattr(x, metric) > than)

    def update(self, attr: str, values: Iterable[Any]) -> None:
        """Update the specified attribute of each agent in the sequence with the corresponding value in the given iterable.

        Parameters:
            attr:
                The name of the attribute to update.
            values:
                An iterable of values to update the attribute with. Must be the same length as the sequence.

        Raises:
            ValueError:
                If the length of the values iterable does not match the length of the sequence.
        """
        self._is_same_length(cast(Sized, values), rep_error=True)
        for agent, val in zip(self, values):
            setattr(agent, attr, val)

    def split(self, where: NDArray[Any]) -> List[ActorsList[A]]:
        """Split actors into N+1 groups at specified positions.

        Parameters:
            where: Array of indices where splits should occur.

        Returns:
            List of ActorsList instances, one for each split group.

        Example:
            ```python
            actors = model.agents.all()  # 10 actors
            groups = actors.split([3, 7])  # Split at indices 3 and 7
            # Returns 3 groups: [0:3], [3:7], [7:10]
            ```
        """
        split: List[NDArray[Any]] = np.hsplit(np.array(self), where)
        return [ActorsList(self._model, group) for group in split]

    def array(self, attr: str) -> np.ndarray:
        """将所有 actor 的指定属性转换为 numpy 数组。

        Parameters:
            attr: 要转换为 numpy 数组的属性名称。

        Returns:
            包含所有 actor 指定属性的 numpy 数组。
        """
        return np.array(self.get(attr))

    def apply(self, ufunc: Callable, *args: Any, **kwargs: Any) -> np.ndarray:
        """对序列中的所有 actor 应用函数。

        Parameters:
            ufunc: 要应用于每个 actor 的函数。
            *args: 传递给函数的位置参数。
            **kwargs: 传递给函数的关键字参数。

        Returns:
            应用函数到每个 actor 的结果数组。
        """
        return np.array(self.map(ufunc, *args, **kwargs))

    def trigger(self, func_name: str, *args: Any, **kwargs: Any) -> np.ndarray:
        """调用序列中所有 actor 上具有给定名称的方法。

        Parameters:
            func_name: 要在每个 actor 上调用的方法的名称。
            *args: 传递给方法的位置参数。
            **kwargs: 传递给方法的关键字参数。

        Returns:
            在每个 actor 上调用方法的结果数组。
        """
        return np.array(self.map(func_name, *args, **kwargs))

    def item(
        self, how: HOW_TO_SELECT = "item", index: int = 0, default: Optional[A] = ...
    ) -> Optional[A]:
        """Get a single actor from the list.

        This method provides convenient access to a single actor from the list
        using different selection strategies.

        Parameters:
            how: Selection method. Options:
                - 'item': Get actor at specified index (default)
                - 'only': Get the only actor, raise error if list doesn't contain exactly one
            index: Index of actor to retrieve when how='item'. Defaults to 0.

        Returns:
            The selected actor, or None if index is out of range (for 'item' method).

        Raises:
            ValueError: If how is not a valid selection method or if 'only' method
                is used but list doesn't contain exactly one actor.

        Example:
            ```python
            # Get first actor
            first = actors.item()

            # Get second actor
            second = actors.item(index=1)

            # Ensure exactly one actor
            solo = single_actor_list.item(how='only')
            ```
        """
        if how == "only":
            return get_only_item(self, default=default)
        if how == "item":
            return self[index] if len(self) > index else None
        raise ValueError(f"Invalid how method '{how}'.")

    @property
    def random(self) -> ListRandom:
        """返回一个 ListRandom 实例，用于随机操作。

        Returns:
            ListRandom: 用于随机操作的实例，使用与 AgentSet 相同的随机数生成器。
        """
        return ListRandom(self._model, self)

    @random.setter
    def random(self, random: np.random.Generator) -> None:
        """Intentionally a no-op.

        mesa's `AgentSet.__init__` assigns `self.random`, which would clash
        with the getter above. Discarding it is safe because the `ListRandom`
        the getter returns already delegates to `model.random` -- so mesa's
        `shuffle` / `shuffle_do` / `select` draw from the same seeded stream
        they would have gotten from the assignment.
        """

    @property
    def is_cells(self) -> bool:
        """Check if this list contains cells (PatchCell) rather than regular actors.

        Returns:
            True if all elements are PatchCell instances (or subclasses), False otherwise.
            Returns False for empty lists or mixed/actor-only lists.

        Example:
            ```python
            cells = model.nature.grid.cells_lst
            print(cells.is_cells)  # True

            agents = model.agents
            print(agents.is_cells)  # False
            ```
        """
        if len(self) == 0:
            return False
        # Lazy import to avoid circular dependency
        from abses.space.cells import PatchCell

        return all(isinstance(elem, PatchCell) for elem in self)

    @property
    def is_actors(self) -> bool:
        """Check if this list contains regular actors rather than cells.

        Returns:
            True if all elements are regular Actor instances (or subclasses), False otherwise.
            Returns False for empty lists or mixed/cell-only lists.

        Example:
            ```python
            cells = model.nature.grid.cells_lst
            print(cells.is_actors)  # False

            agents = model.agents
            print(agents.is_actors)  # True
            ```
        """
        if len(self) == 0:
            return False
        # Lazy import to avoid circular dependency
        from abses.agents.actor import Actor
        from abses.space.cells import (
            PatchCell,  # Exclude cells since they inherit ActorProtocol
        )

        return all(
            isinstance(elem, Actor) and not isinstance(elem, PatchCell) for elem in self
        )

    @property
    def is_mixed(self) -> bool:
        """Check if this list contains both cells and actors.

        Returns:
            True if the list contains both PatchCell and Actor instances.

        Example:
            ```python
            mixed_list = ActorsList(model, [cell1, actor1, cell2])
            print(mixed_list.is_mixed)  # True
            ```
        """
        if len(self) == 0:
            return False
        # Lazy import to avoid circular dependency
        from abses.agents.actor import Actor
        from abses.space.cells import PatchCell

        has_cells = any(isinstance(elem, PatchCell) for elem in self)
        has_actors = any(
            isinstance(elem, Actor) and not isinstance(elem, PatchCell) for elem in self
        )
        return has_cells and has_actors
