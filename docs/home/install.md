---
title: install
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
---

## Install the package

Install with pip or your favorite PyPI package manager.

```shell
pip install abses
```

## Check out tutorials

We suggest to read our documentation in this order:

1. [Read this paper to get familiar with our main novelty.](../wiki/paper.md)
2. [Know the basic structure for organizing your model.](../tutorial/lessons/organize_model_structure.ipynb)
3. [Get know how `ABSESpy` controls ticks and mock real-world time.](../tutorial/lessons/time_control.ipynb)
4. [Write your custom classes of Agent based on our advanced framework](../tutorial/lessons/human_behavior_simulation.ipynb)

## Check API references when building your model

- Programming the [nature module](../api/nature.md) at first.
- In nature module, you may need custom [`PatchCell`](../api/cells.md)
- Introducing your custom agents (actors in social-ecological system context) by [referring this](../api/agents.md).
- Considering what decisions your agents need to make, apply our advanced decision-making framework. You may need to check the docs of [`Decision`](../api/decisions.md).
- Learn to create, manage, and operate your agents by referring [`AgentsContainer`](../api/container.md) and [`ActorsList`](../api/sequences.md).
- Relate your model to real time by [`TimeDriver`](../api/time.md).
