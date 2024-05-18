#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
行动者容器，集中保存行动者。
Container for actors.
"""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    Optional,
    Type,
    Union,
    cast,
)

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

import geopandas as gpd
from loguru import logger
from shapely.geometry.base import BaseGeometry

from abses._bases.base_container import _AgentsContainer
from abses._bases.errors import ABSESpyError
from abses.actor import Actor
from abses.sequences import ActorsList
from abses.tools.func import IncludeFlag, clean_attrs, make_list

if TYPE_CHECKING:
    from abses.cells import PatchCell
    from abses.main import MainModel

ActorTypes: TypeAlias = Union[Type[Actor], Iterable[Type[Actor]]]
Actors: TypeAlias = Union[Actor, ActorsList, Iterable[Actor]]
UniqueID: TypeAlias = Union[str, int]


class _ModelAgentsContainer(_AgentsContainer):
    """AgentsContainer for the MainModel."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._unique_ids: Dict[str, int] = {}

    def _check_unique_id(
        self, unique_id: Optional[UniqueID], breed: str
    ) -> UniqueID:
        if unique_id is None:
            unique_id = f"{breed}[{self._unique_ids[breed]}]"
            self._unique_ids[breed] += 1
        if not isinstance(unique_id, (int, str)):
            raise ABSESpyError(
                f"Unique ID should be an integer or string, got {type(unique_id)}."
            )
        if unique_id in self.get().array("unique_id"):
            raise ABSESpyError(f"Unique ID {unique_id} already exists.")
        return unique_id

    def _check_crs(self, gdf: gpd.GeoDataFrame) -> bool:
        if gdf.crs:
            gdf.to_crs(self.crs, inplace=True)
        else:
            gdf.set_crs(self.crs, inplace=True)
        return self.crs == gdf.crs

    def _new_one(
        self,
        unique_id: Optional[UniqueID] = None,
        geometry: Optional[BaseGeometry] = None,
        agent_cls: type[Actor] = Actor,
        **kwargs,
    ) -> Actor:
        if geometry and not isinstance(geometry, BaseGeometry):
            raise TypeError("Geometry must be a Shapely Geometry")
        unique_id = self._check_unique_id(unique_id, breed=agent_cls.breed)
        agent = agent_cls(
            unique_id=unique_id,
            model=self.model,
            geometry=geometry,
            crs=self.model.nature.crs,
            **kwargs,
        )
        self.add(agent)
        self.model.schedule.add(agent)
        return agent

    def register(self, actor_cls: Type[Actor]) -> None:
        """Registers a new breed of actors.

        Parameters:
            actor_cls:
                The class of the actor to register.
                It can be a single class, or an iterable of classes.
                Once a breed is registered,
                it will be added to all the containers of the model globally.
                It means, it's not necessary to register the same breed again.

        Raises:
            ValueError:
                If the breed is already registered.
        """
        breed = actor_cls.breed
        if breed in self._model.breeds:
            raise ValueError(f"{breed} is already registered.")
        setattr(self._model, "breeds", actor_cls)
        self._unique_ids[breed] = 0

    def new(
        self,
        breed_cls: Type[Actor] = Actor,
        num: int = 1,
        singleton: bool = False,
        **kwargs: Any,
    ) -> Union[Actor, ActorsList[Actor]]:
        """Create one or more actors of the given breed class.

        Parameters:
            breed_cls:
                The breed class of the actor(s) to create.
            num:
                The number of actors to create. Defaults to 1.
            singleton (bool, optional):
                Whether to create a singleton actor. Defaults to False.
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
        # check if the breed class is registered, if not, register it.
        self.check_registration(breed_cls, register=True)
        objs = []
        # create actors.
        for _ in range(num):
            agent = self._new_one(agent_cls=breed_cls, **kwargs)
            objs.append(agent)
        # return the created actor(s).
        actors_list: ActorsList[Actor] = ActorsList(
            model=self.model, objs=objs
        )
        logger.debug(f"{self} created {num} {breed_cls.__name__}.")
        return cast(Actor, actors_list.item()) if singleton else actors_list

    def new_from_gdf(
        self,
        gdf: gpd.GeoDataFrame,
        unique_id: Optional[str] = None,
        agent_cls: type[Actor] = Actor,
        attrs: IncludeFlag = False,
    ) -> ActorsList[Actor]:
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
        # 检查创建主体的数据标识是否唯一，若唯一则设置为索引
        if unique_id:
            gdf = gdf.set_index(unique_id, verify_integrity=True)
        # 如果还没有注册这种主体，那么注册一下
        self.check_registration(agent_cls, register=True)
        # 检查坐标参考系是否一致
        self._check_crs(gdf)
        # 看一下哪些属性是需要加入到主体的
        geo_col = gdf.geometry.name
        set_attributes = clean_attrs(gdf.columns, attrs, exclude=geo_col)
        if not isinstance(set_attributes, dict):
            set_attributes = {col: col for col in set_attributes}
        # 创建主体
        agents = []
        for index, row in gdf.iterrows():
            geometry = row[geo_col]
            new_agent = self._new_one(geometry=geometry, unique_id=index)

            for col, name in set_attributes.items():
                setattr(new_agent, name, row[col])
            agents.append(new_agent)
        # 添加主体到模型容器里
        self.add(agents)
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
        self._cell = cell

    def __str__(self) -> str:
        return "CellAgents"

    def _add_one(self, agent: Actor) -> None:
        if agent.on_earth and agent not in self:
            e1 = f"{agent} is on another cell thus cannot be added."
            e2 = "You may use 'actor.move.to()' to change its location."
            e3 = "Or you may use 'actor.move.off()' before adding it."
            raise ABSESpyError(e1 + e2 + e3)
        super()._add_one(agent)
        agent.at = self._cell

    def remove(self, agent: Actor) -> None:
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
        if agent.at is not self._cell:
            raise ABSESpyError(f"{agent} is not on this cell.")
        self[agent.breed].remove(agent)
        del agent.at

    def new(
        self,
        breed_cls: Type[Actor] = Actor,
        num: int = 1,
        singleton: bool = False,
        **kwargs: Any,
    ) -> Actor | ActorsList:
        """Creates a new actor or a list of actors of the given breed class.
        The created actors are added to both the cell and the model's global container.

        Parameters:
            breed_cls:
                The breed class of the actor(s) to create.
            num:
                The number of actors to create. Defaults to 1.
            singleton:
                Whether to create a singleton actor. Defaults to False.
            **kwargs:
                Additional keyword arguments to pass to the actor constructor.

        Returns:
            The created actor(s).
        """
        # Using model's container to create a list of actors
        new_actors = self.model.agents.new(breed_cls, num, singleton, **kwargs)
        # move the actors to the cell
        for a in make_list(new_actors):
            a.move.to(self._cell)
        return new_actors
