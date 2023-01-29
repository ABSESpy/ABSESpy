---
title: user_guide
authors: SongshGeo
date: 2023-01-10
long_name: Agent-Based Social-ecological systems Modelling Framework in Python
name: AB-SESpy
state: open
banner_icon: 💻
banner: "https://songshgeo-picgo-1302043007.cos.ap-beijing.myqcloud.com/uPic/abses_github_repo.svg"
banner_y: 0.52
SES: social-ecological systems
github: https://github.com/SongshGeo
email: songshgeo@gmail.com
website: https://cv.songshgeo.com
banner_x: 0.70193
---
# Structures

The overall structure of `ABSESpy` is shown in the following diagram:

![structure](https://songshgeo-picgo-1302043007.cos.ap-beijing.myqcloud.com/uPic/structure.png){width: 400px, align: center}

Three main components `BaseHuman`, `BaseNature` and `MainModel` are included. Generally, users need to write their `sub-modules` for the operation of ecosystems or the operation of social systems, as well as the behaviour of `actors`. Once the model has been developed, the `mediator` will coordinate the running of the model and output the simulation to a log. The `Experiment` helps the user run the model to perform sensitivity of specific parameters.

## Model

- First of all, get started with a simple [model demo](notebooks/model.ipynb).
- [Management of model parameters using `yaml` configuration files](notebooks/parameters.ipynb).

## Nature

- [Load the geographic dataset](notebooks//nature/geodata.ipynb) as the space in which the subject operates and the patch variables that the subject can access based on its location.
- [Manipulate `Patch` object for better spatial analysis](notebooks//nature/patch.ipynb)

## Human

- Understanding of the structure of the `ABSESpy` [management and storage `Actor` (i.e., agents)](notebooks//human/actors.ipynb)
- Defining the [collections of actors, rules of action, perception](notebooks//human/rules.ipynb) ... as if they were real people
- Applying [Cognition, Contagion and behavioral Response (CCR Framework)](../docs/background.md#human-behaviour-framework) with `ABSESpy`, here is an [demo model](notebooks/human/CCR_example.ipynb).

## Experiment

- Run the model repeatedly to test the sensitivity of a parameter. This function from agentpy is used. [Please refer to here](https://agentpy.readthedocs.io/en/latest/guide_ema.html).
