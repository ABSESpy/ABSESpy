#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from itertools import combinations
from typing import (
    TYPE_CHECKING,
    Any,
    Iterable,
    List,
    Literal,
    Optional,
    Tuple,
    Type,
    Union,
    overload,
)

import numpy as np

from abses._bases.errors import ABSESpyError
from abses.tools.func import make_list

if TYPE_CHECKING:
    from abses.actor import Actor
    from abses.main import MainModel
    from abses.sequences import ActorsList

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

WHEN_EMPTY: TypeAlias = Literal["raise exception", "return None"]


class ListRandom:
    """Create a random generator from an `ActorsList`"""

    def __init__(self, model: MainModel[Any, Any], actors: ActorsList) -> None:
        self.model = model
        self.actors = actors
        self.seed = model.random.random() * 100
        self.generator = np.random.default_rng(seed=int(self.seed))

    def _to_actors_list(self, objs: Iterable) -> ActorsList:
        from abses.sequences import ActorsList

        return ActorsList(self.model, objs=objs)

    def _when_empty(self, when_empty: WHEN_EMPTY) -> None:
        if when_empty not in ("raise exception", "return None"):
            raise ValueError(
                f"Unknown value for `when_empty` parameter: {when_empty}"
            )
        if when_empty == "raise exception":
            raise ABSESpyError(
                "Trying to choose an actor from an empty `ActorsList`."
            )

    def clean_p(self, prob: Union[np.ndarray, str]) -> np.ndarray:
        """Clean the probabilities.
        Any negative values, NaN values, or zeros will be recognized as in-valid probabilities.
        For all valid probabilities, normalize them into a prob-array (the sum is equal to 1.0).

        Parameters:
            prob:
                An array-like numbers of probabilities.

        Returns:
            The probabilities after cleaned.

        Example:
        ```
        >>> clean_p([0, 0])
        >>> [0.5, 0.5]

        >>> clean_p([-1, np.nan])
        >>> [0.5, 0.5]

        >>> clean_p([3, 2])
        >>> [0.6, 0.4]
        ```
        """
        if isinstance(prob, str):
            prob = self.actors.array(attr=prob)
        prob = np.array(make_list(prob))
        length = len(prob)
        prob = np.nan_to_num(prob)
        prob[prob < 0] = 0.0
        total = prob.sum()
        prob = prob / total if total else np.repeat(1 / length, length)
        return prob

    @overload
    def choice(
        self,
        size: int = 1,
        prob: np.ndarray | None = None,
        replace: bool = False,
        as_list: bool = False,
        when_empty: WHEN_EMPTY = "raise exception",
    ) -> Actor | ActorsList[Actor]:
        ...

    def choice(
        self,
        size: int = 1,
        prob: np.ndarray | None | str = None,
        replace: bool = False,
        as_list: bool = False,
        when_empty: WHEN_EMPTY = "raise exception",
    ) -> Optional[Actor | ActorsList[Actor]]:
        """Randomly choose one or more actors from the current self object.

        Parameters:
            size:
                The number of actors to choose. Defaults to 1.
            prob:
                A list of probabilities for each actor to be chosen.
                If None, all actors have equal probability.
                If is a string, will use the value of this attribute as the prob.
                Defaults to None.
            replace:
                Whether to sample with replacement. Defaults to True.
            as_list:
                Whether to return the result as a list of actors. Defaults to False.

        Returns:
            An Actor or an ActorList of multiple actors.

        Notes:
            Given the parameter set size=1 and as_list=False, a single Actor object is returned.
            Given the parameter set size>1 and as_list=False, a Self (ActorsList) object is returned.

        Raises:
            ValueError:
                If size is not a positive integer.
            ABSESpyError:
                Not enough actors to choose in this `ActorsList`.
        """
        instances_num = len(self.actors)
        if instances_num == 0:
            self._when_empty(when_empty=when_empty)
            return None
        if not isinstance(size, int):
            raise ValueError(f"{size} isn't an integer size.")
        if instances_num < size and not replace:
            raise ABSESpyError(
                f"Trying to choose {size} actors from {self.actors}."
            )
        if prob is not None:
            prob = self.clean_p(prob=prob)
        chosen = self.generator.choice(
            self.actors, size=size, replace=replace, p=prob
        )
        return (
            chosen[0]
            if size == 1 and not as_list
            else self._to_actors_list(chosen)
        )

    def new(
        self,
        actor_cls: Type[Actor],
        num: int = 1,
        replace: bool = False,
        prob: np.ndarray | None = None,
        **kwargs,
    ) -> ActorsList[Actor]:
        """Randomly creating new agents for a given actor type."""
        cells = self.choice(as_list=True, size=num, replace=replace, prob=prob)
        objs = cells.apply(
            lambda c: c.agents.new(
                breed_cls=actor_cls, singleton=True, **kwargs
            )
        )
        return self._to_actors_list(objs)

    def link(
        self, link: str, p: float = 1.0, mutual: bool = True
    ) -> List[Tuple[Actor, Actor]]:
        """Random build links between actors.

        Parameters:
            link:
                Name of the link.
            p:
                Probability to generate a link.

        Returns:
            A list of tuple, in each tuple, there are two actors who got linked.

        Example:
            ```
            # generate three actors
            actors = model.agents.new(Actor, 3)
            # with `probability=1`, all possible actor-actor links would be generated.
            >>> actors.random.link('test', p=1)
            >>> a1, a2, a3 = actors
            >>> assert a1.link.get('test) == [a2, a3]
            >>> assert a2.link.get('test) == [a1, a3]
            >>> assert a3.link.get('test) == [a1, a2]
            ```
        """
        linked_combs = []
        for source, target in list(combinations(self.actors, 2)):
            if np.random.random() < p:
                source.link.to(target, link_name=link, mutual=mutual)
                linked_combs.append((source, target))
        return linked_combs
