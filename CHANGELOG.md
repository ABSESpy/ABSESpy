
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
