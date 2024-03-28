
<a id='changelog-0.5.4'></a>
# 0.5.4 — 2024-03-28

## Documentation changes

- [x] #docs📄 Line 24: 'research' not 'researches'
- [x] #docs📄 Line 44: rather than 'et al.' maybe use actual words (e.g. 'and others') so as not to confuse against the file suffixes which are similar abbreviations
- [x] #docs📄  Line 55: What do you mean by 'practicing' here? This doesn't seem right. Please edit to clarify
- [x] #docs📄  Lines 57-65: I'm surprised these three points (Perceptions, Decision-making, Response) don't match the words used in Fig 2 (Options, Evaluate, Behaviour). Or are the latter three (in the Fig) all part of the 'decision-making' step? Aligning the steps in the list with the figure would be useful, I think
- [x] #docs📄  Line 76: I think 'vary' should be 'varying'
- [x] #docs📄  Line 93: 'more accurate' - this is a relative statement, so please clarify 'more accurate' than what?
- [x] #docs📄  Line 99: ( wang2022h? )) is not included in the reference list
- [x] #docs📄  Line 100: it's good that you recognise the similarity here to `AgentPy` but you don't then clearly explain how `absespy` is beneficial for SES researchers - maybe you could highlight the explicit functionality for representing the 'nature' side of CHANS (`AgentPy` really focuses on the 'human' side).
- [x] #docs📄  Line 108: 'merely heuristic' - I think this is a little over-critical of NetLogo, which can incorporate 'real-world' (I think you mean 'empirical'?) data although not at the scale `absespy` could. I suggest you edit here to focus on the value of `absespy` for working with large-scale, empirical data so that models can run more efficiently than would be possible for the same data in NetLogo. You might also highlight your `TimeDriver` module which is a benefit over NetLogo's more simple 'ticks'

- [x] #docs📄  L105 & L151: netlogo and Netlogo should be NetLogo
- [x] #docs📄  L42, L98, L101 & L153 : mesa-geo and Mesa-geo should be Mesa-Geo
- [x] #docs📄  L95, L97, L98, L102, L129 & L153 : mesa should be Mesa
- [x] #docs📄  L96: abce should be ABCE
- [x] #docs📄  L128, L148 & L154: python should be Python

- [x] #docs📄 Update project readme
- [x] #docs📄 Improve JOSS paper overall.

<a id='changelog-0.5.3'></a>
# 0.5.3 — 2024-03-26

## Fixed bugs

- [x] #bug🐛 Only alive actors can apply default methods by decorator `alive_required` now.
- [x] #bug🐛 now moving has a return to control continue to move or not.
- [x] #bug🐛 now update the position attribute correctly after moving
- [x] #bug🐛 fixing release drafter to the latest version

<a id='changelog-0.5.2'></a>
# 0.5.2 — 2024-03-26

## Performance improvements

- [x] #zap⚡️ improve getting performance from container

## New Features

- [x] #feat✨ now getting link name can be with a default empty return
- [x] #feat✨ getting an attr value from a `ActorsList`
- [x] #feat✨ before moving, `Actor` may do something
- [x] #feat✨ possible to control max length when customize `PatchCell`
- [x] #feat✨  getting an item or None from `ActorsList` or container

<a id='changelog-0.5.1'></a>
# 0.5.1 — 2024-03-20

## Documentation changes

- [x] #docs📄 Update all tutorials
- [x] #docs📄 Update readme

## Refactoring

- [x] #refactor♻️ Refactoring some tests
- [x] #refactor♻️ Remove some died codes.

<a id='changelog-0.5.0'></a>
# 0.5.0 — 2024-03-12

## Performance improvements

- [x] #zap⚡️ improve code formats
- [x] #build🏗 upgrade dependencies and using typing-extension

## New Features

- [x] #feat✨ Agents now can use `move.to` a random `pos` on a layer
- [x] #feat✨ Random choose now can select from an empty list
- [x] #feat✨ actors' movement by new proxy class

## Documentation changes

- [x] #docs📄 updating docs notebooks for beginners
- [x] #docs📄 refactoring the structure of api docs
- [x] #docs📄 improve docs format

## Fixed bugs

- [x] #bug🐛 use typing_extensions to make abses compatible to python 3.9
- [x] #bug🐛 alter nature now behaves correctly
- [x] #bug🐛 fixing `Main Nature` `total_bounds` check ambigious
- [x] #bug🐛 fixing `random.replace` arg doesn't work problem

## Refactoring

- [x] #refactor♻️ separate `_CellAgentsContainer` and `AgentsContainer`
- [x] #refactor♻️ using default schedule and data collector, but compatible to attrs config
- [x] #refactor♻️ AgentsContainer private and not singleton anymore
- [x] refactoring `nature`, `Actor` `links` and its tests
- [x] store agents by container in PatchCell
- [x] use `get`, `set` methods to control the actor's behaviors

<a id='changelog-0.4.2'></a>
# 0.4.2 — 2024-01-11

## Refactoring

- [x] #refactor♻️ Refactoring data collector tests to `tests/conftest.py`

## Fixed bugs

- [x] #bug🐛 Data collector strings are collected now.

<a id='changelog-0.4.1'></a>
# 0.4.1 — 2024-01-11

## Documentation changes

- [x] #docs📄 Update project README

## Fixed bugs

- [x] #bug🐛 Fix `mkdocs` CI bug

<a id='changelog-0.4.0'></a>
# 0.4.0 — 2024-01-11

## New Features

- [x] #feat✨ `run_model`  function can set steps now.
- [x] #feat✨ Better logging by loguru

## Documentation changes

- [x] #docs📄 Re-structuring documentations
- [x] #docs📄 Update get-started
- [x] #docs📄 Actors' movement

<a id='changelog-0.3.5rc'></a>
# 0.3.5rc — 2023-12-05

## Fixed bugs

- [x] #bug🐛 fix `AttributeError: 'super' object has no attribute 'random'`

<a id='changelog-0.3.5'></a>
# 0.3.5 — 2023-12-05

## New Features

- [x] #feat✨ `random.choice` in random module
- [x] #feat✨ `data-collector` module for collecting data

## Documentation

- [x] #docs📄 Update API documentation of `random`
- [x] #docs📄 Add a citation of `wang2022h`

<a id='changelog-0.3.4'></a>
# 0.3.4 — 2023-12-01

## Fixed bugs

- [x] #bug🐛 (modules): :bug: fixed the geometry links behave not stably.

<a id='changelog-0.3.3'></a>
# 0.3.3 — 2023-11-29

## Fixed bugs

- [x] #bug🐛 fixing `random.choice` triggered error : `'super' object has no attribute 'random'`

<a id='changelog-0.3.2'></a>
# 0.3.2 — 2023-11-29

## New Features

- [ ] #feat✨ Generate random links between actors with the possibility

<a id='changelog-0.3.1'></a>
# 0.3.1 — 2023-11-28

## Performance improvements

- [x] #build🏗 Un-pin the dependencies and upgrade

<a id='changelog-0.3.0'></a>
# 0.3.0 — 2023-11-11

## Documentation changes

- [x] #docs📄 Refine the api documentation
- [x] #docs📄 Add a simple paper to introduce the package
- [x] #docs📄 Update readme to highlight some features.
- [x] #docs📄 Add an example of Hotelling model.

## New Features

- [x] #feat✨ Introduce, test, documentation an example of decisions framework

## Refactoring

- [x] #refactor♻️ Some small refactoring when polishing api documents

<a id='changelog-0.2.1.alpha'></a>
# 0.2.1.alpha — 2023-11-07

## Documentation changes

- [x] #docs📄 introduce the new feature: real-world time control
- [x] #docs📄 Architectural Elegance for Modular Socio-Ecological Systems Modeling

## Refactoring

- [x] #refactor♻️ using `loguru` for logs
- [x] #refactor♻️ using `pendulum` for solving `TimeDriver`
- [x] #refactor♻️ [使用logrue来控制日志](https://github.com/Delgan/loguru)

## Fixed bugs

- [x] #bug🐛 fixing twice logging bug
- [x] #bug🐛 hot-fix infinitely model runing
- [x] #bug🐛 Twice logging.

# v-0.1.0 🎉

## New Features

- [x] #feat✨  #agent🤖️  Create, remove, add `Actor` in `Container`
- [x] #feat✨  #agent🤖️  Select `Actor` in `ActorsList` by adding selection syntax
- [x] #feat✨  #agent🤖️  read attributes from current `PatchCell`.
- [x] #feat✨  #Nature🌍 Automatically reads spatial data as raster variables
- [x] #feat✨  #Nature🌍 Adding, removing `Actors` into nature spaces.

## Documentation changes

- [x] #docs📄  #project🎉 Logging.
- [x] #docs📄 #project🎉 Basic introduction of `ABSESpy`

# v-0.1.1 🎉

## Documentation changes

- [x] #docs📄 update README document

# v-0.1.2 🎉

## Fixed bugs

- [x] #bug🐛 fixed log setup twice

# v-0.2.0.alpha 🎉

- [x] #refactor♻️ Remove `variable` class and replace it with `DynamicVariable`.
- [x] #refactor♻️ Remove `TimeDriverManager` and adding type hint to `TimeDriver`
- [x] #build🏗 #project🎉 Removed dependence of `AgentPy`.
