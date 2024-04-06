#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
这个模块储存一些
"""

import logging
from typing import Any, Callable, List

import numpy as np
from scipy import ndimage

from abses.tools.regex import CAMEL_NAME

logger = logging.getLogger(__name__)


def get_buffer(
    array: np.ndarray,
    radius: int = 1,
    moor: bool = False,
    annular: bool = False,
) -> np.ndarray:
    """Get a buffer around the array.

    Parameters:
        array:
            The array to get buffer from.
        radius:
            The radius of the buffer.
        moor:
            If True, use moor connectivity (8 neighbors include Diagonal pos).
            Otherwise use von Neumann (4 neighbors).
        annular:
            If True, return an annular buffer.
            e.g., if radius is 2, the result will be a ring with radius 1-2.

    Raises:
        ValueError:
            If radius is not positive or not int type.

    Returns:
        The buffer mask array.
    """
    if radius <= 0 or not isinstance(radius, int):
        raise ValueError(f"Radius must be positive int, not {radius}.")
    connectivity = 2 if moor else 1
    struct = ndimage.generate_binary_structure(2, connectivity)
    result = ndimage.binary_dilation(
        array, structure=struct, iterations=radius
    )
    if annular and radius > 1:
        interior = ndimage.binary_dilation(
            array, structure=struct, iterations=radius - 1
        )
        return result & np.invert(interior)
    return result


def make_list(element: Any, keep_none: bool = False) -> List:
    """Turns element into a list of itself if it is not of type list or tuple."""

    if element is None and not keep_none:
        element = []  # Convert none to empty list
    if not isinstance(element, (list, tuple, set, np.ndarray)):
        element = [element]
    elif isinstance(element, (tuple, set)):
        element = list(element)

    return element


def iter_func(elements: str) -> Callable:
    """
    A decorator broadcasting function to all elements if available.

    Parameters:
        elements:
            attribute name where object store iterable elements.
            All element in this iterable object will call the decorated function.

    Returns:
        The decorated class method.
    """

    def broadcast(func: Callable) -> Callable:
        def broadcast_func(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            if not hasattr(self, elements):
                return result
            for element in getattr(self, elements):
                getattr(element, func.__name__)(*args, **kwargs)
            return result

        return broadcast_func

    return broadcast


def camel_to_snake(name: str) -> str:
    """Convert camel name to snake name.

    Parameters:
        name:
            The name to convert.

    Returns:
        The converted name.
    """
    # https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
    return CAMEL_NAME.sub("_", name).lower()
