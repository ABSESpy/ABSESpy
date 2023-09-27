![abses_github_repo](https://songshgeo-picgo-1302043007.cos.ap-beijing.myqcloud.com/uPic/abses_github_repo.png)

[![license](https://img.shields.io/github/license/songshgeo/absespy)](http://www.apache.org/licenses/) ![downloads](https://img.shields.io/github/downloads/songshgeo/absespy/total) ![codesize](https://img.shields.io/github/languages/code-size/songshgeo/absespy) ![tag](https://img.shields.io/github/v/tag/songshgeo/absespy)
[![github](https://img.shields.io/badge/Website-SongshGeo-brightgreen.svg)](https://cv.songshgeo.com/) ![stars](https://img.shields.io/github/stars/songshgeo/absespy?style=social) [![twitter](https://img.shields.io/twitter/follow/shuangsong11?style=social)](https://twitter.com/shuangsong11)

<!-- Language: [English Readme](#) | [简体中文](README_ch) -->

`ABSESpy` makes it easier to build artificial **[Social-ecological systems](https://songshgeo.github.io/ABSESpy/docs/about/)** with real **GeoSpatial datasets** and fully incorporate **human behaviour**.

## Why `ABSESpy`?

**Several characteristics of Agent-Based model (ABM) make it an essential method for social-ecological systems (SES) research:**

1. It focuses on the change of an SES over time from mutual adaptations of agents and their environments.
2. its ability to generate emergent system-level outcomes from micro-level interactions and macro-level feedback.
3. its ability to represent the diversity and heterogeneity of human and non-human actors and the spatial characteristics of an SES ...

However, there is currently no modelling framework that **combines geo-spatial data and actor behaviour** (`actor` is the term for agents in the SES framework) well. `ABSESpy` is designed for spatial modelling that **couples human and nature** by:

- Modelling environment for agents with **[geo data](https://songshgeo.github.io/ABSESpy/tutorial/notebooks/nature/geodata/)**: `Shapefile`, `GeoTiff`, `NetCDF`.
- Modelling **[human behaviour](https://songshgeo.github.io/ABSESpy/tutorial/notebooks/human/CCR_example/)** of agents with [cognition, contagion and responses](https://songshgeo.github.io/ABSESpy/docs/background/#human-behaviour-framework).
- Easily manage all [parameters, arguments](https://songshgeo.github.io/ABSESpy/tutorial/notebooks/parameters/), and variables with a `yaml` settings file.

## Install

Install with pip or your favourite PyPI package manager.
```
pip install abses
```

## Basic usage & Documents

You can see how to use `ABSESpy` in these simple [tutorials](https://songshgeo.github.io/ABSESpy/tutorial/user_guide/):

1. [Organize an Agent-based model](https://songshgeo.github.io/ABSESpy/tutorial/notebooks/model/) and [easily manage parameters](https://songshgeo.github.io/ABSESpy/tutorial/notebooks/parameters/).
2. Using [geo-spatial data](https://songshgeo.github.io/ABSESpy/tutorial/notebooks/nature/geodata/) as the environment.
3. Simply applying a [human behavior framework](https://songshgeo.github.io/ABSESpy/tutorial/notebooks/human/CCR_example/).

<img src="https://songshgeo-picgo-1302043007.cos.ap-beijing.myqcloud.com/uPic/DQg0xJ.jpg" alt="Drawing" style="width: 600px;"/>

Access the [full Documentation here](https://songshgeo.github.io/ABSESpy/).

## Get in touch

- **For enthusiastic developers and contributors**, all contributions, bug reports, bug fixes, documentation improvements, enhancements, and ideas are welcome.
- **For SES researchers**, welcome to use this package in social-ecological system (SES) studies. If you have a model published, feel free to contribute it to our model library through [mailing list](https://groups.google.com/g/absespy).

If you need any help when using `ABSESpy`, don't hesitate to get in touch with us through:

- Ask usage questions ("How to do?") on [_GitHub_ Discussions](https://github.com/SongshGeo/ABSESpy/discussions).
- Report bugs, suggest features or view the source code [on _GitHub_](https://github.com/SongshGeo/ABSESpy/issues).
- For less well-defined questions or ideas or to announce other projects of interest to xarray users, use the [mailing list](https://groups.google.com/g/absespy).

## License

Copyright 2023, `ABSESpy` [Shuang Song](https://cv.songshgeo.com/)

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

[https://www.apache.org/licenses/LICENSE-2.0](https://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

`ABSESpy` bundles portions of `AgentPy`, `pandas`, `NumPy` and `Xarray`; the full text of these licenses is included in the licenses directory.
