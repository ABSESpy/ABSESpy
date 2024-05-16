#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""Logging module.
"""

import sys

from loguru import logger

logger.remove(0)
FORMAT = "[{time:HH:mm:ss}][{module}] {message}\n"


def formatter(record) -> str:
    """Customize formatter."""
    return "{message}\n" if record["extra"].get("no_format") else FORMAT


logger.add(
    sys.stderr,
    format=formatter,
    level="WARNING",
    colorize=True,
)


def log_session(title: str, msg: str = ""):
    """logging a new module session."""
    first_line = "\n" + "=" * 20 + "\n"
    center_line = f"  {title}  ".center(20, "-")
    end_line = "\n" + "=" * 20 + "\n"
    ending = "".center(20, "-")
    logger.bind(no_format=True).info(
        first_line + center_line + end_line + msg + ending
    )


def setup_logger_info():
    """Set up logger."""
    line_equal = "".center(40, "=") + "\n"
    line_star = "".center(40, "·") + "\n"
    content = "  ABSESpy Framework  ".center(40, "*") + "\n"
    msg = line_equal + line_star + content + line_star + line_equal
    logger.bind(no_format=True).info(msg)
