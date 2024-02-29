#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from itertools import combinations
from typing import TYPE_CHECKING, Iterable, List, Tuple, overload

import numpy as np

from abses.errors import ABSESpyError
from abses.tools.func import make_list

if TYPE_CHECKING:
    from abses.actor import Actor
    from abses.main import MainModel
    from abses.sequences import ActorsList


class ListRandom:
    """Create a random generator from an `ActorsList`"""

    def __init__(self, model: MainModel, actors: ActorsList) -> None:
        self.model = model
        self.actors = actors
        self.seed = getattr(model, "_seed", 0)
        self.generator = np.random.default_rng(seed=int(self.seed))

    def _to_actors_list(self, objs: Iterable) -> ActorsList:
        from abses.sequences import ActorsList

        return ActorsList(self.model, objs=objs)

    def _when_empty(self, when_empty: str) -> str:
        if when_empty not in ("raise exception", "return None"):
            raise ValueError(
                f"Unknown value for `when_empty` parameter: {when_empty}"
            )
        if when_empty == "raise exception":
            raise ABSESpyError(
                "Trying to choose an actor from an empty `ActorsList`."
            )
        return None

    @overload
    def clean_p(self, p: str) -> np.ndarray:
        ...

    def clean_p(self, prob: np.ndarray) -> np.ndarray:
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

    def choice(
        self,
        size: int = 1,
        prob: np.ndarray | None | str = None,
        replace: bool = False,
        as_list: bool = False,
        when_empty: str = "raise exception",
    ) -> Actor | ActorsList:
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
            return self._when_empty(when_empty=when_empty)
        if not isinstance(size, int):
            raise ValueError(f"{size} isn't an integer size.")
        if not instances_num or (instances_num < size & ~replace):
            raise ABSESpyError(
                f"Trying to choose {size} actors from an `ActorsList` {self.actors}."
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

    def link(self, link: str, p: float = 1.0) -> List[Tuple[Actor, Actor]]:
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
            actors = model.agents.create(Actor, 3)
            # with `probability=1`, all possible actor-actor links would be generated.
            >>> actors.random.link('test', p=1)
            >>> a1, a2, a3 = actors
            >>> assert a1.linked('test) == [a2, a3]
            >>> assert a2.linked('test) == [a1, a3]
            >>> assert a3.linked('test) == [a1, a2]
            ```
        """
        linked_combs = []
        for actor1, actor2 in list(combinations(self.actors, 2)):
            if np.random.random() < p:
                actor1.link_to(actor2, link=link, mutual=True)
                linked_combs.append((actor1, actor2))
        return linked_combs
