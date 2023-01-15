badgets:

- python versions:
- pypi package
- downloads/month
- stars
- blog
- follow twitter

![pixel_abses2](https://songshgeo-picgo-1302043007.cos.ap-beijing.myqcloud.com/uPic/pixel_abses2.svg)

Language: [English Readme](#) | [简体中文](README_ch)

![p50LQ2](https://songshgeo-picgo-1302043007.cos.ap-beijing.myqcloud.com/uPic/p50LQ2.jpg)

ABSESpy makes it easier to build artificial **Social-ecological systems** with GeoSpatial datasets.
- Create the environment for agents with **geo data**: `Shapefile`, `GeoTiff`, `NetCDF`.
- **Actors** as agent templates from the **IAD framework** and **MoHuB** framework.
- Easily manage all parameters, arguments, and variables with a `yaml` settings file.
- Generate **reporting** documents, logging, and experiment reports of simulations.
- Integrated auto experiment with sensitivity analysis and basic visualisation methods.

## Installing
Install with pip or your favourite PyPI package manager.
```
pip install abses
```

Run the following to test ABSESpy successfully installed on your terminal:
```
abses --verson
```

## Basic usage

```yaml
world:
	width: 22
	height: 22
	boundary: 1
time:
	start: 2000-01-01
	freq: M
	end: 2020-01-01
nature:
	map: xxx/xxx/map.shp
	resolution:

human:
	admins: 3
	farmers: 30

```

Then create the model logic in Python:
```python
from abses import Model, Actor

# subclass from the Model, creating an artificial Social-ecological System.
class ArtificialSES(Model):

	def initialize(self):
		pass

	def setup(self):
		# setup after loading parameters
		actors = self.human.generate_actors(Actor, n=3)
		self.nature.add_actors(actors, how=randomly)
		# each actor owns a piece of land by Voronoi
		self.nature.allocating(actors, algorithm=voronoi)

	def update(self):
		pass

	def step(self):
		pass

	def end(self):
		pass

model, nature, human, agents = Model.to_objects()
```

Simulation:
Climate change:

Actors' decisions:

See documents for more usage examples.

## Why agent-based modelling with SES?
### Agent-based model applications in SES research:
1. xx
2. xx
3. xx


## Testing model

We provide a testing model, install data from [here]() and run tests.

## Projects using ABSESpy

Welcome to use this package in your research. If you need any help when using **ABSESpy**, don't hesitate to get in touch with me through songshgeo@gmail.com
- Agriculture and water use in the Yellow River Basin, China
