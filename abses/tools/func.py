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
from functools import wraps
from typing import Any, Callable, List, Optional, Tuple, TypeVar, cast

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from scipy import ndimage

from abses.tools.regex import CAMEL_NAME

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


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


def with_axes(
    decorated_func: Optional[F] = None, figsize: Tuple[int, int] = (6, 4)
) -> Callable[..., Any]:
    """装饰一个函数/方法，如果该方法接受一个参数叫'ax'并且为None，为其增加一个默认的绘图布。

    Parameters:
        decorated_func:
            被装饰的函数，检查是否有参数传递给装饰器，若没有则返回装饰器本身。
        figsize:
            图片画布的大小，默认宽度为6，高度为4。

    Returns:
        被装饰的函数
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ax = kwargs.get("ax", None)
            if ax is None:
                _, ax = plt.subplots(figsize=figsize)
                kwargs["ax"] = cast(Axes, ax)
                result = func(*args, **kwargs)
                return result
            else:
                return func(*args, **kwargs)

        return wrapper

    # 检查是否有参数传递给装饰器，若没有则返回装饰器本身
    return decorator(decorated_func) if decorated_func else decorator


def set_null_values(arr: np.ndarray, mask: np.ndarray):
    """
    Set null values in an array based on a boolean mask and the array's data type.

    Parameters:
        arr:
            The input array that can contain float or strings.
        mask:
            A boolean array where True indicates that a null value should be set.

    Returns:
        The modified array with null values set.
    """
    if arr.shape != mask.shape:
        raise ValueError(f"Mismatching shape {mask.shape} and {arr.shape}.")
    # Check if the dtype is float or integer
    if arr.dtype.kind in {"f", "i"}:
        null_value = np.nan
    # Unicode string
    elif arr.dtype.kind == "U":
        null_value = ""
    # # Byte string
    elif arr.dtype.kind == "S":
        null_value = b""
    else:
        raise ValueError(f"Unsupported data type {arr.dtype}")
    arr[mask] = null_value
    return arr
