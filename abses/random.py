#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from itertools import combinations
from typing import TYPE_CHECKING, List, Tuple

import numpy as np

if TYPE_CHECKING:
    from abses.actor import Actor
    from abses.sequences import ActorsList


class ListRandom:
    """Create a random generator from an `ActorsList`"""

    def __init__(self, actors: ActorsList, seed=None) -> None:
        self.actors = actors
        self.seed = seed
        self.generator = np.random.default_rng(seed=int(self.seed))

    def choice(self) -> Actor:
        """Random choice an element from ActorsList."""
        # TODO refactor ActorsList.random_choose to here
        return self.generator.choice(self.actors)

    def link(self, link: str, p: float = 1.0) -> List[Tuple[Actor, Actor]]:
        """Random build links between actors."""
        linked_combs = []
        for actor1, actor2 in list(combinations(self.actors, 2)):
            if np.random.random() < p:
                actor1.link_to(actor2, link=link, mutual=True)
                linked_combs.append((actor1, actor2))
        return linked_combs
