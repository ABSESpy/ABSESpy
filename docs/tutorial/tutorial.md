# Tutorial

<!-- 这里，我们提供了一系列基于Jupyter Notebook的教程，展示实际利用 ABSESpy 开发可能碰到的需求及其解决策略。 -->

Here, we provide a series of tutorials based on [Jupyter Notebook], demonstrating the potential needs and solutions when developing with `ABSESpy` in practice. We expect you to have read through [Quick Start] guide and that you have assessed whether `ABSESpy` is [the right software for you]. Three levels of tutorials are available below:

> [!INFO]In Progress
> This document is a work in progress if you see any errors, or exclusions or have any problems, please [get in touch with us](https://github.com/absespy/ABSESpy/issues).

## :hatching_chick: Beginner level

You're looking to create and operate a basic model by `ABSESpy` framework. Wondering what constitutes a "simple" model? Explore the [NetLogo model repository]; you'll find many classic yet easy-to-understand examples there.

<div class="grid" markdown>

[:material-book: __B01__](beginner/get_started.ipynb) Welcome to review the quick start in notebook anytime.
{ .card }

[:material-book: __B02__](beginner/organize_model_structure.ipynb) Organize your model structure with elegance.
{ .card }

[:material-book: __B03__](beginner/time_control.ipynb) Keep your model in time with the real world.
{ .card }

[:material-book: __B04__](beginner/manage_parameters.ipynb) Separate configuration and model logic with a config file.
{ .card }

[:material-book: __B05__](beginner/actors.ipynb) Manage actors better with different containers.
{ .card }

[:material-book: __B06__](beginner/movement.ipynb) Move your agents in the artificial world.
{ .card }

[:material-book: __B07__](beginner/hotelling_tutorial.ipynb) Your first full model example, a classic heuristic model[^1].
{ .card }

[:material-book: __B08__](beginner/fire_tutorial.ipynb) A classic agent-based model.
{ .card }

[:material-book: __B09__](beginner/predation_tutorial.ipynb) Wolf-Sheep predation model.
{ .card }

> :material-book: __Huh__ ... More tutorials in this level are coming soon.

</div>

## :horse_racing_tone1: Advanced level

You have gained a thorough understanding of the agent-based model. Now, you are not just satisfied with heuristic models[^1], you aspire to undertake a larger project to solve real-world SES problems.

<div class="grid" markdown>

[:material-book: __A01__](advanced/human_behavior_simulation.ipynb) How to apply an advanced [human behavior simulation framework]?
{ .card }

[:material-book: __A02__](advanced/geodata.ipynb) Including real-world geographic datasets.
{ .card }

> :material-book: __Huh__ ... More tutorials in this level are coming soon.

</div>

## :scientist: Completing level

You have already established your own model and confirmed that it does not have major logical issues. You need help with batch experiments, data analysis, plotting, parameter sensitivity analysis, and visualization.

<div class="grid" markdown>

<!-- [:material-book: __A01__](advanced/human_behavior_simulation.ipynb) How to apply an advanced [human behavior simulation framework]?
{ .card } -->

> :material-book: __Huh__ ... More tutorials in this level are coming soon.

</div>

[^1]:
    Heuristic models are streamlined strategies used to tackle complex issues when precise formulas or solutions aren't feasible. These models rely on heuristic methods, practical tactics that may not always yield the best solution but offer a satisfactory one within an acceptable time limit.

<!-- Links -->
  [Jupyter Notebook]: https://jupyter.org/
  [Quick Start]: ../home/get_started.md
  [the right software for you]: ../home/guide_checklist.md
  [NetLogo model repository]: https://ccl.northwestern.edu/netlogo/models/
  [human behavior simulation framework]: ../wiki/concepts/CCR.md
