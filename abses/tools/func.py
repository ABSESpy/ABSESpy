#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/
import logging
from typing import Iterable, List

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


def opfunc_using_attr(attr: str, binary_op: bool) -> callable:
    """
    wrap a operation method of a custom class, for using its 'attribution' in calculation.

    Args:
        attr (str): which attribute of the class to use in calculation.
        binary_op (bool): if the wrapping operation method is binary or unary.

    Returns:
        callable: a wrapped bound method.

    Examples:
        class Calculation:
            def __init__(self):
                self.attr = 1

        cal = Calculation()

        cal + 1
        >>> TypeError: 'unsupported operand type(s)' ...

        # wraping the '__add__' method.
        opname = '__add__'
        wrapper = opfunc_using_attr('attr', binary_op=True)
        wrapped_func = wrapper(getattr(1, opname))
        setattr(cal.__class__, opname, wrapped_func)

        cal + 1 == 2
        >>> 2
    """

    # wraping binary operation functions.
    def wrap_binary_opfunc(func):
        def new_func(self, other):
            opfunc = getattr(getattr(self, attr), func.__name__)
            if issubclass(other.__class__, self.__class__):
                return opfunc(getattr(other, attr))
            else:
                return opfunc(other)

        return new_func

    # wraping unary operation functions.
    def wrap_unary_opfunc(func):
        def new_func(self):
            opfunc = getattr(getattr(self, attr), func.__name__)
            return opfunc()

        return new_func

    if binary_op:
        return wrap_binary_opfunc
    else:
        return wrap_unary_opfunc


# https://zhuanlan.zhihu.com/p/515284250
_binary_opfunc = (
    "__add__",
    "__sub__",
    "__mul__",
    "__truediv__",
    "__floordiv__",
    "__mod__",
    "__divmod__",
    "__pow__",
    "__radd__",
    "__rsub__",
    "__rmul__",
    "__rtruediv__",
    "__rfloordiv__",
    "__rmod__",
    "__rdivmod__",
    "__rpow__",
    "__lshift__",
    "__rshift__",
    "__and__",
    "__xor__",
    "__or__",
)

_unary_opfunc = (
    "__neg__",
    "__pos__",
    "__abs__",
    "__invert__",
)


def wrap_opfunc_to(obj: object, attr: str) -> List[str]:
    """
    Overwrite an object's all operation functions, using its attribute in future's calculations.

    Args:
        obj (object): any object to be wrapped.
        attr (str): object's attribute name.

    Returns:
        List[str]: successful wrapped operation functions' name.

    Examples:
        class MyClass(object):
            def __init__(self, attr: any):
                self.attr: any = attr
        int_obj = MyClass(1)
        str_obj = MyClass('test')
        wrap_opfunc_to
    """

    def wrap_opfunc(binary_op):
        func = getattr(getattr(obj, attr), opname, None)
        if func is None:
            return False
        else:
            wrapper = opfunc_using_attr(attr, binary_op=binary_op)
            setattr(obj.__class__, opname, wrapper(func))
            return True

    successful_wrapped = []
    for opname in _binary_opfunc:
        wrapped = wrap_opfunc(True)
        if wrapped:
            successful_wrapped.append(opname.strip("_"))
    for opname in _unary_opfunc:
        wrapped = wrap_opfunc(False)
        if wrapped:
            successful_wrapped.append(opname.strip("_"))
    return successful_wrapped
