#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
Container for actors.
"""

from __future__ import annotations

import contextlib
from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Type,
    Union,
    cast,
)

with contextlib.suppress(ImportError):
    import networkx as nx
try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

import geopandas as gpd
import pyproj
from loguru import logger
from mesa import Model
from mesa.agent import AgentSet
from shapely.geometry.base import BaseGeometry

from abses._bases.errors import ABSESpyError
from abses.actor import Actor, Breeds
from abses.links import get_node_unique_id
from abses.random import ListRandom
from abses.sequences import ActorsList
from abses.tools.func import IncludeFlag, clean_attrs

if TYPE_CHECKING:
    from abses.cells import PatchCell
    from abses.main import MainModel

ActorTypes: TypeAlias = Union[Type[Actor], Iterable[Type[Actor]]]
Actors: TypeAlias = Union[Actor, ActorsList, Iterable[Actor]]
UniqueID: TypeAlias = Union[str, int]
UniqueIDs: TypeAlias = List[Optional[UniqueID]]


class _AgentsContainer:
    """AgentsContainer for the main model."""

    def __init__(
        self,
        model: MainModel[Any, Any],
        max_len: None | int = None,
    ):
        if not isinstance(model, Model):
            raise TypeError(f"{model} is not a Mesa Model.")
        self._model: MainModel = model
        self._agents = model._all_agents
        self._max_length = max_len

    def __len__(self) -> int:
        return len(self._agents)

    def __str__(self) -> str:
        return f"<Handling [{len(self)}]Agents for {self.model.name}>"

    def __contains__(self, actor: object) -> bool:
        return actor in self._agents

    def __iter__(self) -> Iterator[Actor]:
        return iter(self._agents)

    def __getitem__(self, breeds: Optional[Breeds]) -> ActorsList[Actor]:
        """Get agents by breed(s).

        Args:
            breeds: Single breed (str or Type) or list of breeds to retrieve

        Returns:
            AgentSet containing all agents of the specified breed(s)

        Example:
            container['Breed1']  # by string name
            container[Breed1]    # by class type
            container[['Breed1', 'Breed2']]  # multiple breeds by name
            container[[Breed1, Breed2]]      # multiple breeds by type
        """
        if isinstance(breeds, (list, tuple)):
            # 对多个 breeds 进行合并
            agents = []
            for breed in breeds:
                breed_type = self._get_breed_type(breed)
                agents.extend(self._model.agents_by_type[breed_type])
            return ActorsList(model=self.model, objs=agents)

        # 单个 breed 的情况
        if not isinstance(breeds, (str, type)):
            raise TypeError(f"{breeds} is not a string or a type.")
        breed_type = self._get_breed_type(breeds)
        return ActorsList(
            model=self.model, objs=self._model.agents_by_type[breed_type]
        )

    def __getattr__(self, name: str) -> Any:
        """Get an attribute from the container."""
        if not name.startswith("_") and hasattr(self._agents, name):
            return getattr(self._agents, name)
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    @property
    def crs(self) -> pyproj.CRS:
        """Returns the current CRS."""
        return self._model.nature.crs

    @property
    def model(self) -> MainModel[Any, Any]:
        """The ABSESpy model where the container belongs to."""
        return self._model

    @property
    def random(self) -> ListRandom:
        """The random number generator."""
        return ListRandom(actors=self, model=self.model)

    @property
    def is_full(self) -> bool:
        """Whether the container is full."""
        return (
            False
            if self._max_length is None
            else len(self) >= self._max_length
        )

    @property
    def is_empty(self) -> bool:
        """Check whether the container is empty."""
        return len(self) == 0

    def _get_breed_type(self, breed: str | Type[Actor]) -> Type[Actor]:
        """Convert breed name to breed type if necessary."""
        if isinstance(breed, str):
            # 如果是字符串，在已注册的类型中查找对应名称的类
            for breed_type in self._model.agents_by_type.keys():
                if breed_type.__name__ == breed:
                    return breed_type
            raise ABSESpyError(f"Breed '{breed}' not found")
        return breed

    def _add_one(self, agent: Actor) -> None:
        pass

    def _check_full(self) -> None:
        """Add one agent to the container."""
        if self.is_full:
            raise ABSESpyError(f"{self} is full.")
        if self.model.agents.is_full:
            raise ABSESpyError(f"{self.model.agents} is full.")

    def add(self, agent: Actor) -> None:
        """Add one agent to the container."""
        self._check_full()
        self._add_one(agent)
        self._agents.add(agent)

    def _new_one(
        self,
        geometry: Optional[BaseGeometry] = None,
        agent_cls: type[Actor] = Actor,
        **kwargs,
    ) -> Actor:
        if geometry and not isinstance(geometry, BaseGeometry):
            raise TypeError("Geometry must be a Shapely Geometry")
        if not isinstance(agent_cls, type) or not issubclass(agent_cls, Actor):
            raise TypeError(f"{agent_cls} is not a subclass of Actor.")
        self._check_full()
        agent = agent_cls(
            model=self.model,
            geometry=geometry,
            crs=self.model.nature.crs,
            **kwargs,
        )
        self._add_one(agent)
        return agent

    def new(
        self,
        breed_cls: Type[Actor] = Actor,
        num: Optional[int] = None,
        singleton: Optional[bool] = None,
        **kwargs: Any,
    ) -> Union[Actor, ActorsList[Actor]]:
        """Create one or more actors of the given breed class.

        Parameters:
            breed_cls:
                The breed class of the actor(s) to create. Defaults to `Actor`.
            num:
                The number of actors to create. Only positive integer is allowed.
                Defaults to None, which will be set to 1 and singleton to True.
            singleton (bool, optional):
                Whether to create a singleton actor.
                If singleton is True, the return value will be an actor instance.
                Otherwise, it will be an `AgentSet` instance.
                Defaults to False.
                If `num` is None, this parameter will be ignored.
            **kwargs:
                Additional keyword arguments to pass to the actor constructor.

        Returns:
            The created actor(s).

        Example:
            ```python
            from abses import Actor, MainModel
            model = MainModel()
            actor = model.agents.new(singleton=True)
            >>> type(actor)
            >>> Actor

            actors = model.agents.new(singleton=False)
            >>> type(actors)
            >>> ActorsList
            ```
        """
        # create actors.
        if num is None:
            num = 1
            if singleton is None:
                singleton = True
        if not isinstance(num, int) or num < 0:
            raise ValueError(
                f"Number of actors to create must be a non-negative integer. Got {num}."
            )
        if num == 0:
            return ActorsList(model=self.model, objs=[])
        # 创建主体
        objs = []
        for _ in range(num):
            agent = self._new_one(agent_cls=breed_cls, **kwargs)
            objs.append(agent)
        # return the created actor(s).
        actors_list: ActorsList[Actor] = ActorsList(
            model=self.model, objs=objs
        )
        logger.debug(f"{self} created {num} {breed_cls.__name__}.")
        return (
            cast(Actor, actors_list.item())
            if singleton is True
            else actors_list
        )

    def remove(self, agent: Actor) -> None:
        """Remove the given agent from the container."""
        if agent.on_earth:
            raise ABSESpyError(
                f"{agent} is still on the earth. Use `agent.remove()` instead."
            )
        self._model.deregister_agent(agent)

    def has(self, breeds: Optional[Breeds] = None) -> int:
        """Whether the container has the breed of agents.

        Parameters:
            breeds:
                The breed(s) of agents to search.

        Returns:
            int:
                The number of agents of the specified breed(s).

        Example:
            ```python
            from abses import Actor, MainModel

            class Actor1(Actor):
                # breed 1
                pass

            class Actor2(Actor):
                # breed 2
                pass

            model = MainModel()
            model.agents.new(Actor, singleton=True)
            model.agents.new(Actor1, num=2)
            model.agents.new(Actor2, num=3)

            model.agents.has('Actor1')
            >>> 2
            model.agents.has(['Actor1', 'Actor2'])
            >>> 5
            ```
        """
        if breeds is None:
            return len(self)
        return len(self[breeds])

    def select(
        self,
        selection: Callable | str | Dict[str, Any] | None = None,
        agent_type: Optional[Type[Actor] | str] = None,
        **kwargs: Any,
    ) -> ActorsList:
        """Select actors that match the given selection criteria.

        Parameters:
            selection:
                The selection criteria.
                It can be a string, a callable, or a dictionary.
            **kwargs:
                Additional arguments to pass to the `AgentSet.select()` method, in addition to `filter_func`.
                - at_most (int | float, optional): The maximum amount of agents to select. Defaults to infinity.
                  - If an integer, at most the first number of matching agents are selected.
                  - If a float between 0 and 1, at most that fraction of original the agents are selected.
                - inplace (bool, optional): If True, modifies the current AgentSet; otherwise, returns a new AgentSet. Defaults to False.
                - agent_type (type[Agent], optional): The class type of the agents to select. Defaults to None, meaning no type filtering is applied.
                - n (int): deprecated, use at_most instead
        """
        if isinstance(agent_type, (str, type)):
            kwargs["agent_type"] = self._get_breed_type(agent_type)

        def check_attr(agent, attr, value=True):
            return getattr(agent, attr) == value

        if isinstance(selection, str):
            filter_func = partial(check_attr, attr=selection, value=True)
            agents_set = self._agents.select(filter_func=filter_func, **kwargs)
        elif any([callable(selection), selection is None]):
            agents_set = self._agents.select(filter_func=selection, **kwargs)
        elif isinstance(selection, dict):
            agents_set = self._agents
            for attr, value in selection.items():
                filter_func = partial(check_attr, attr=attr, value=value)
                agents_set = agents_set.select(
                    filter_func=filter_func, **kwargs
                )
        else:
            raise TypeError(f"{selection} is not valid selection criteria.")
        return ActorsList(model=self.model, objs=agents_set)


class _ModelAgentsContainer(_AgentsContainer):
    """AgentsContainer for the MainModel."""

    def _check_crs(self, gdf: gpd.GeoDataFrame) -> bool:
        if gdf.crs:
            gdf.to_crs(self.crs, inplace=True)
        else:
            gdf.set_crs(self.crs, inplace=True)
        return self.crs == gdf.crs

    def new_from_graph(
        self,
        graph: "nx.Graph",
        link_name: str,
        actor_cls: Type[Actor] = Actor,
        **kwargs,
    ):
        """Create a set of new agents from networkx graph."""
        actors = []
        mapping = {}
        for node, attr in graph.nodes(data=True):
            unique_id = get_node_unique_id(node=node)
            actor = self._new_one(unique_id, agent_cls=actor_cls, **attr)
            actors.append(actor)
            mapping[unique_id] = actor
        self.model.human.add_links_from_graph(
            graph, link_name=link_name, mapping_dict=mapping, **kwargs
        )
        return ActorsList(model=self.model, objs=actors)

    def new_from_gdf(
        self,
        gdf: gpd.GeoDataFrame,
        agent_cls: type[Actor] = Actor,
        attrs: IncludeFlag = False,
        **kwargs,
    ) -> ActorsList[Actor]:
        # TODO: 这个方法需要适配到最新的 Mesa 版本
        """Create actors from a `geopandas.GeoDataFrame` object.

        Parameters:
            gdf:
                The `geopandas.GeoDataFrame` object to convert.
            unique_id:
                A column name, to be converted to unique index
                of created geo-agents (Social-ecological system Actors).
            agent_cls:
                Agent class to create.

        Raises:
            ValueError:
                If the column specified by `unique_id` is not unique.

        Returns:
            An `ActorsList` with all new created actors stored.
        """
        # 检查坐标参考系是否一致
        self._check_crs(gdf)
        # 看一下哪些属性是需要加入到主体的
        geo_col = gdf.geometry.name
        set_attributes = clean_attrs(gdf.columns, attrs, exclude=geo_col)
        if not isinstance(set_attributes, dict):
            set_attributes = {col: col for col in set_attributes}
        # 创建主体
        agents = []
        for _, row in gdf.iterrows():
            geometry = row[geo_col]
            new_agent = self._new_one(
                geometry=geometry,
                agent_cls=agent_cls,
                **kwargs,
            )
            new_agent.crs = self.crs

            for col, name in set_attributes.items():
                setattr(new_agent, name, row[col])
            agents.append(new_agent)
        # 添加主体到模型容器里
        return ActorsList(model=self.model, objs=agents)


class _CellAgentsContainer(_AgentsContainer):
    """Container for agents located at cells."""

    def __init__(
        self,
        model: MainModel[Any, Any],
        cell: PatchCell,
        max_len: int | None = None,
    ):
        super().__init__(model, max_len)
        self._agents = AgentSet([], random=model.random)
        self._cell = cell

    def _add_one(self, agent: Actor) -> None:
        super()._add_one(agent)
        if agent.on_earth and agent not in self:
            e1 = f"{agent} is on {agent.at} thus cannot be added."
            e2 = "You may use 'actor.move.to()' to change its location."
            e3 = "Or you may use 'actor.move.off()' before adding it."
            raise ABSESpyError(e1 + e2 + e3)
        self._agents.add(agent)
        agent.at = self._cell

    def remove(self, agent: Optional[Actor] = None) -> None:
        """Remove the given agent from the cell.
        Generally, it stores all the agents on this cell.
        Therefore, it is not recommended to use this method directly.
        Consider to use `actor.move.off()` to let the actor leave this cell instead.

        Parameters:
            agent:
                The agent (actor) to remove.

        Raises:
            ABSESpyError:
                If the agent is not on this cell.
        """
        if agent is None:
            self._agents.clear()
            return
        assert isinstance(agent, Actor), f"{agent} is not an Actor."
        if agent.at is not self._cell:
            raise ABSESpyError(f"{agent} is not on this cell.")
        self._agents.remove(agent)
        del agent.at
