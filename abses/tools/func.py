#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/
import logging
import re
from typing import Any, Iterable

import numpy as np
from scipy import ndimage

logger = logging.getLogger(__name__)


CAMEL_NAME = re.compile(r"(?<!^)(?=[A-Z])")


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


def camel_to_snake(name):
    """Convert camel name to snake name."""
    # https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
    return CAMEL_NAME.sub("_", name).lower()
