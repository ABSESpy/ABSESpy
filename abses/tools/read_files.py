#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import logging
import os
from typing import Iterable

from abses.tools.func import make_list

logger = logging.getLogger(__name__)


def get_files_in_folder(
    dir_path,
    suffix: str | Iterable[str] = "",
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
