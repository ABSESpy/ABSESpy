#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/
import logging
from typing import Any, Iterable

import numpy as np
from scipy import ndimage

logger = logging.getLogger(__name__)


def get_buffer(
    array: np.ndarray,
    radius: int = 1,
    moor: bool = False,
    annular: bool = False,
) -> np.ndarray:
    """Get a buffer around the array."""
    if radius <= 0:
        raise ValueError(f"Radius must be positive, not {radius}.")
    connectivity = 2 if moor else 1
    struct = ndimage.generate_binary_structure(2, connectivity)
    result = ndimage.binary_dilation(
        array, structure=struct, iterations=radius
    )
    if annular and radius > 1:
        interior = ndimage.binary_dilation(
            array, structure=struct, iterations=radius - 1
        )
        return result & ~interior
    return result


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


def norm_choice(
    a: Iterable[any], size: int = None, p=None, replace=False
) -> Any:
    """
    A more robust random chooser.

    Args:
        a (Iterable[any]): An iterable instance to choose.
        size (int, optional): size of the choice. Defaults to None.
        p (_type_, optional): probability. Defaults to None.
        replace (bool, optional): _description_. Defaults to False.

    Returns:
        Any: _description_
    """
    p = np.array(make_list(p))
    possible_entries = (p > 0).sum()
    if possible_entries == 0:
        p = None
    else:
        p = np.where(p > 0, p, 0.0)
        p /= p.sum()
    if p is None or replace is True:
        return np.random.choice(a, size=size, p=p, replace=replace)
    # 如果有概率的实体 少于要选择的实体，优先返回
    if size is None:
        return np.random.choice(a, p=p, replace=False)
    elif possible_entries < size:
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


def iter_func(elements: str) -> callable:
    """
    A decorator broadcasting function to all elements if available.

    elements:
        elements (str): attribute name where object store iterable elements.
        All element in this iterable object will call the decorated function.
    """

    def broadcast(func: callable) -> callable:
        def broadcast_func(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            if not hasattr(self, elements):
                return result
            for element in getattr(self, elements):
                getattr(element, func.__name__)(*args, **kwargs)
            return result

        return broadcast_func

    return broadcast
