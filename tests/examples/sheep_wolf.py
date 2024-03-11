#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""狼羊草模型
"""

from abses import Actor, MainModel, PatchCell, PatchModule


class Grass(PatchCell):
    """Custom patch cell class"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.empty = False
        self._countdown = 5

    def grow(self):
        """Grow some grass on the cell every 5 ticks."""
        # countdown on brown patches: if you reach 0, grow some grass
        if self.empty is True:
            if self._countdown <= 0:
                self.empty = False
                self._countdown = 5
            else:
                self._countdown -= 1


class Animal(Actor):
    """Custom animal"""

    def __init__(self, *args, **kwargs):
        Actor.__init__(self, *args, **kwargs)
        self.energy = 5

    def step(self):
        pass

    def update(self):
        """Update the animal's state."""
        # consume energy
        self.energy -= 1
        if self.energy <= 0:
            self.die()

    def reproduce(self):
        """Reproduce if there's enough energy."""
        if self.random.random() < self.params.rep_rate:
            self.energy /= 2
            self.at.agents.create(self.__class__)


class Wolf(Animal):
    """Custom wolf."""

    def step(self):
        self.move.random()
        self.eat_sheep()
        self.reproduce()
        self.update()

    def eat_sheep(self):
        """If there is a sheep in the cell, eat it and gain 2 energy."""
        sheep = self.at.agents.select("Sheep")
        if a_sheep := sheep.random.choice(when_empty="return None"):
            a_sheep.die()
            self.energy += 2


class Sheep(Animal):
    """Custom sheep."""

    def step(self):
        self.move.random()
        self.eat_grass()
        self.reproduce()
        self.update()

    def eat_grass(self):
        """If there is a grass in the cell, eat it and gain 2 energy."""
        if self.get("empty", target="world") is False:
            self.energy += 2
            self.set("empty", True, target="world")


class WolfSheepModel(MainModel):
    """Wolf-Sheep predation tutorial model."""

    def setup(self):
        # initialize a grid
        grassland: PatchModule = self.nature.create_module(
            how="from_resolution",
            shape=self.params.shape,
            name="grassland",
            cell_cls=Grass,
        )
        # add sheep and wolves
        self.agents.create(Wolf, self.params.n_wolves)
        self.agents.create(Sheep, self.params.n_sheep)
        # without a specific position, agents will move randomly on the layer.
        self.agents.apply(lambda x: x.move.to(pos="random", layer=grassland))

    def step(self):
        self.agents.trigger("step")
        self.nature.grassland.trigger("grow")
        self.check_end()

    def check_end(self):
        """Check if the model should stop."""
        # end model
        if not self.agents.get("Sheep"):
            self.running = False
        elif not self.agents.get("Wolf"):
            self.running = False
        elif len(self.actors.select("Sheep")) >= 400:
            self.running = False
