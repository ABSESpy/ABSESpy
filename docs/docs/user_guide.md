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

- First of all, to [Model Structure](#TODO)

## Nature

## Human

## Experiment
