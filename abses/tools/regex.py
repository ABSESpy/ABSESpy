#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
This module contains some commonly used regular expressions for checking names.
这个模块里存储一些检查名称常用的正则表达式。
"""
import re

# 模块名称应该符合蛇形命名法，且不能以下划线开头
# Module name is snake case and should not start with an underscore
# https://www.cnblogs.com/mrlonely2018/p/15650605.html
MODULE_NAME = re.compile(r"[a-z][a-z0-9_]*")

# 类名应该符合驼峰命名法
# Class name should be in camel case
CAMEL_NAME = re.compile(r"(?<!^)(?=[A-Z])")
