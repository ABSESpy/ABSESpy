---

kanban-plugin: basic

---

## Open

- [ ] #docs📄 Adding Simplified Chinese README
- [ ] #test🧪  #build🏗  Test on other Python versions
- [ ] #zap⚡️ #project🎉 Parallel operation (maybe `dask`)
- [ ] #feat✨  #agent🤖️ Actors as agent templates from the **IAD framework** and **MoHuB** framework. TODO Link
- [ ] #zap⚡️ Speed up by [cupy](https://cupy.dev/) or [pypy](https://zhuanlan.zhihu.com/p/435652722).
- [ ] #feat✨ #Nature🌍 Solving nodata
- [ ] #feat✨  Give users an option of real-dates or just a counter
- [ ] #feat✨  MaxLenSet for each cell
- [ ] #docs📄  [[deploy documentation through Vercel with custom domain]]


## Planned

- [ ] #refactor♻️ Using modules to manipulate agent
- [ ] Beginner tutorial: Hotelling's Law #feat✨  #Elias🧑
- [ ] #feat✨  Auto-update dynamic variables
- [ ] #bug🐛 [[Fixing the twice logging bug]]
- [ ] #refactor♻️  [[Use Pendulum instead of `pandas.Period`]]
- [ ] #feat✨ Not allow to appear any same module name


## Testing

- [ ] #feat✨  #examples🌰 Upload the first complete case of a large model
- [ ] #feat✨  #agent🤖️ Store the relationships with other `Acotor`
- [ ] #feat✨  #human👨  The module automatically generates complex networks for all main bodies


## Published

**完成**
- [x] #refactor♻️ Remove `variable` class and replace it with `DynamicVariable`.
- [x] #refactor♻️ Remove `TimeDriverManager` and adding type hint to `TimeDriver`
- [x] #bug🐛 #examples🌰 fix the zero division in `water_quota` example @{📅 2023-09-30}
- [x] #docs📄 [[Initial API documentation is completed]] #Elias🧑‍💻
- [x] #build🏗 #project🎉 Removed dependence of `AgentPy`.


***

## 归档

- [x] #feat✨  #agent🤖️  Create, remove, add `Actor` in `Container`
- [x] #feat✨  #agent🤖️  Select `Actor` in `ActorsList` by adding selection syntax
- [x] #feat✨  #agent🤖️  read attributes from current `Patch`.
- [x] #feat✨  #Nature🌍 Automatically reads spatial data as raster variables
- [x] #feat✨  #Nature🌍 Adding, removing `Actors` into nature spaces.
- [x] #docs📄  #project🎉 Logging.
- [x] #docs📄 #project🎉 Basic introduction of `ABSESpy`
- [x] #build🏗 #project🎉 Building framework with `AgentPy`

%% kanban:settings
```
{"kanban-plugin":"basic"}
```
%%