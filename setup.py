#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="abses",
    license="BSD 3-Clause",
    author="Shuang Song",
    author_email="songshgeo@gmail.com",
    description="Agent-based social-ecological system framework in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://agentpy.readthedocs.io/",
    download_url="https://github.com/absespy/ABSESpy",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Intended Audience :: Science/Research",
        "Operating System :: OS Independent",
    ],
)
