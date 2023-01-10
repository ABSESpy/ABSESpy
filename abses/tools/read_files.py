#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import os
from typing import Iterable, Optional

import yaml
from numpy import ndarray


def make_list(element, keep_none=False):
    """Turns element into a list of itself
    if it is not of type list or tuple."""

    if element is None and not keep_none:
        element = []  # Convert none to empty list
    if not isinstance(element, (list, tuple, set, ndarray)):
        element = [element]
    elif isinstance(element, (tuple, set)):
        element = list(element)

    return element


def redirect_if_yaml(param: str, nesting: bool = True) -> dict:
    if not type(param) is str:
        return
    if not os.path.isfile(param):
        return param
    if param.endswith(".yaml"):
        settings = parse_yaml(param, nesting)
    else:
        settings = param
    return settings


def parse_yaml(path: Optional[str] = None, nesting: bool = False) -> dict:
    if not path or not path.endswith(".yaml"):
        raise ValueError("Invalid YAML file path: %s" % path)
    else:
        return read_yaml(path, nesting)


def read_yaml(path: str, nesting: bool = True) -> dict:
    """
    Load parameters from yaml settings file.

    Arguments:
        yaml_file -- File path.
        detecting_nesting (bool, optional): wether to detect nesting `yaml` files. Defaults to True.

    Raises:
        KeyError: Cannot find a param by key.
    """
    # Read yaml file
    with open(path, "r", encoding="utf-8") as file:
        yaml_data = file.read()
        params = yaml.load(yaml_data, Loader=yaml.FullLoader)
        file.close()
    if nesting:
        to_update = {}
        for key, value in params.items():
            new_params = redirect_if_yaml(value, nesting=nesting)
            if isinstance(new_params, dict) and new_params:
                to_update[key] = new_params
        params.update(to_update)
    return params


def get_files_in_folder(
    dir_path,
    suffix: "str|Iterable[str]" = "",
    iteration: bool = True,
    full_path: bool = False,
) -> list[str]:
    """
    Read all files in a specific path.

    Args:
        dir_path (str): folder path.
        postfix (str|Iterable[str], optional): valid postfix. Defaults to "".
        iteration (bool, optional): if sub-folders include. Defaults to True.
        full_path (bool, optional): return full path of the files, or just the filename. Defaults to False.

    Raises:
        FileNotFoundError: Invalid dir_path.

    Returns:
        list[str]: list of filenames (default),
        or full path of the files (if full_path) is True.
    """
    if not os.path.isdir(dir_path):
        raise FileNotFoundError(f"{dir_path} not a valid folder.")
    paths = []
    valid_postfix = make_list(suffix)
    if iteration:
        for root, _, files in os.walk(dir_path, topdown=False):
            for filename in files:
                validation = [
                    filename.endswith(suffix) for suffix in valid_postfix
                ]
                if not any(validation):
                    continue
                if full_path:
                    path = os.path.join(root, filename)
                    paths.append(path)
                else:
                    paths.append(filename)
    else:
        filename = os.listdir(dir_path)
        paths.append(os.path.join(dir_path, filename))
    return paths
