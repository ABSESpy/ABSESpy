#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/
import logging
from typing import Iterable

import numpy as np

logger = logging.getLogger(__name__)


def make_list(element, keep_none=False):
    """Turns element into a list of itself
    if it is not of type list or tuple."""

    if element is None and not keep_none:
        element = []  # Convert none to empty list
    if not isinstance(element, (list, tuple, set, np.ndarray)):
        element = [element]
    elif isinstance(element, (tuple, set)):
        element = list(element)

    return element


def norm_choice(a: Iterable[any], size: int = None, p=None) -> any:
    if p is None or len(set(p)) == 0:
        p = np.ones(len(make_list(a)))
    p = np.array(make_list(p), dtype=float)
    negative = p < 0
    if sum(negative) > 0:
        logger.warning(
            f"Input {sum(negative)} p are negative, change to zero when normalizing."
        )
        p[negative] = 0.0
    if all(p == 0):
        p = np.ones(len(make_list(a)))
        logger.warning("Input possibilities are all zeros.")
    p /= p.sum()
    # 如果有概率的实体 少于要选择的实体
    if size is None:
        return np.random.choice(a, p=p)
    possible_entries = len(p[p > 0])
    if possible_entries < size:
        bounds = a[p > 0]
        rand = np.random.choice(
            a[p == 0], size=(size - possible_entries), replace=False
        )
        selected = np.concatenate([bounds, rand])
    else:
        selected = np.random.choice(a, p=p, size=size, replace=False)
    return selected


def unique_list(*args):
    unique = set()
    for lst in args:
        if not isinstance(lst, Iterable):
            raise TypeError("unique_list can only convert iterable to list")
        unique = unique | set(lst)
    return list(unique)
