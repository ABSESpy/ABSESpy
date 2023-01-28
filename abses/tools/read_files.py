#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import logging
import os
from typing import Iterable

import xarray as xr
import yaml

from .func import make_list

logger = logging.getLogger(__name__)


def is_valid_yaml(path: any) -> bool:
    """
    Judge if the input is a valid yaml file path.

    Args:
        path (any): element to judge.

    Returns:
        bool: if is a valid yaml file path, returns True.
    """
    if not isinstance(path, str):
        return False
    elif not path.endswith(".yaml"):
        return False
    elif not os.path.isfile(path):
        raise ValueError(
            f"{path} contains '.yaml' but is not a valid yaml file path."
        )
    else:
        return True


def redirect_yaml(param: dict) -> None:
    """
    Clean dictionary, if valid-yaml file path exists, replace it with a new dictionary.

    Args:
        param (dict): dictionary to clean.
    """
    for key, val in param.items():
        if isinstance(val, dict):
            redirect_yaml(val)
        elif is_valid_yaml(val):
            param[key] = read_yaml(val, True)


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
        redirect_yaml(params)
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
