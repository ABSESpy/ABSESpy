#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""在列表中随机操作主体
"""

from __future__ import annotations

from itertools import combinations
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
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
    from abses.links import LinkingNode
    from abses.main import MainModel
    from abses.sequences import ActorsList

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

WHEN_EMPTY: TypeAlias = Literal["raise exception", "return None"]


class ListRandom:
    """Create a random generator from an `ActorsList`"""

    def __init__(
        self, model: MainModel[Any, Any], actors: Iterable[Any]
    ) -> None:
        self.model = model
        self.actors = self._to_actors_list(actors)
        self.seed = model.random.random() * 100
        self.generator = np.random.default_rng(seed=int(self.seed))

    def _to_actors_list(self, objs: Iterable) -> ActorsList:
        from abses.sequences import ActorsList

        return ActorsList(self.model, objs=objs)

    def _when_empty(
        self, when_empty: WHEN_EMPTY, operation: str = "choice"
    ) -> None:
        if when_empty not in ("raise exception", "return None"):
            raise ValueError(
                f"Unknown value for `when_empty` parameter: {when_empty}"
            )
        if when_empty == "raise exception":
            raise ABSESpyError(
                f"Random operating '{operation}' on an empty `ActorsList`."
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
        else:
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
        as_list: bool = True,
        when_empty: WHEN_EMPTY = "raise exception",
    ) -> ActorsList[LinkingNode]:
        ...

    @overload
    def choice(
        self,
        size: int = 1,
        prob: np.ndarray | None = None,
        replace: bool = False,
        as_list: bool = False,
        when_empty: WHEN_EMPTY = "raise exception",
    ) -> LinkingNode | ActorsList[LinkingNode]:
        ...

    def choice(
        self,
        size: int = 1,
        prob: np.ndarray | None | str = None,
        replace: bool = False,
        as_list: bool = False,
        when_empty: WHEN_EMPTY = "raise exception",
        double_check: bool = False,
    ) -> Optional[LinkingNode | ActorsList[LinkingNode]]:
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
        # 有概率的时候，先清理概率
        if prob is not None:
            prob = self.clean_p(prob=prob)
            valid_prob = prob.astype(bool)
            # 特别处理有概率的主体数量不足预期的情况
            if valid_prob.sum() < size and not replace:
                return self._when_p_not_enough(double_check, valid_prob, size)
        # 其他情况就正常随机选择
        chosen = self.generator.choice(
            self.actors, size=size, replace=replace, p=prob
        )
        return (
            chosen[0]
            if size == 1 and not as_list
            else self._to_actors_list(chosen)
        )

    def _when_p_not_enough(self, double_check, valid_prob, size):
        if not double_check:
            raise ABSESpyError(
                f"Only {valid_prob.sum()} entities have possibility, "
                f"but {size} entities are expected. "
                "Please check the probability settings.\n"
                "If you want to choose with replacement, set `replace=True`.\n"
                "If you want to choose with equal probability, set `prob=None`.\n"
                "If you want to choose the valid entities firstly, "
                "and then choose others equally, set `double_check=True'`."
            )
        first_chosen = self.actors.select(valid_prob)
        others = self.actors.select(~valid_prob)
        remain_size = size - len(first_chosen)
        second_chosen = self.generator.choice(
            others, remain_size, replace=False
        )
        return self._to_actors_list([*first_chosen, *second_chosen])

    def new(
        self,
        actor_cls: Type[Actor],
        actor_attrs: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> ActorsList[Actor]:
        """Randomly creating new agents for a given actor type."""
        if actor_attrs is None:
            actor_attrs = {}
        cells = self.choice(as_list=True, **kwargs)
        objs = cells.apply(
            lambda c: c.agents.new(
                breed_cls=actor_cls, singleton=True, **actor_attrs
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

    def assign(
        self,
        value: float | int,
        attr: str,
        when_empty: WHEN_EMPTY = "raise exception",
    ) -> np.ndarray:
        """Randomly assign a value to each actor."""
        num = len(self.actors)
        if num == 0:
            self._when_empty(when_empty=when_empty, operation="assign")
            return np.array([])
        if num == 1:
            values = np.array([value])
        else:
            # 生成 n-1 个随机切割点
            cuts = np.sort(self.generator.uniform(0, value, num - 1))
            # 将 0 和总面积 X 添加到切割点数组中，方便计算每段区间长度
            full_range = np.append(np.append(0, cuts), value)
            # 计算每个区间的长度，即为每个对象的分配面积
            values = np.diff(full_range)
        # 将分配的值赋予每个对象
        self.actors.update(attr, values)
        return values
