#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from typing import Any, Dict, Union


def parsing_string_selection(selection: str) -> Dict[str, Any]:
    """Parses a string selection expression and returns a dictionary of key-value pairs.

    Parameters:
        selection:
            String specifying which breeds to select.

    Returns:
        selection_dict:
            Parsed output as Dictionary
    """
    selection_dict = {}
    if "==" not in selection:
        return {"breed": selection}
    expressions = selection.split(",")
    for exp in expressions:
        left, right = tuple(exp.split("=="))
        selection_dict[left.strip(" ")] = right.strip(" ")
    return selection_dict


def selecting(actor, selection: Union[str, Dict[str, Any]]) -> bool:
    """Either select the agent according to specified criteria.

    Parameters:
        selection:
            Either a string or a dictionary of key-value pairs that represent agent attributes to be checked against.

    Returns:
        Whether the agent is selected or not
    """
    if isinstance(selection, str):
        selection = parsing_string_selection(selection)
    results = []
    for k, v in selection.items():
        attr = getattr(actor, k, None)
        if attr is None:
            results.append(False)
        elif attr == v or str(attr) == v:
            results.append(True)
        else:
            results.append(False)
    return all(results)
