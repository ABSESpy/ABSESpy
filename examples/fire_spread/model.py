#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
测试野火燃烧模型。
"""
from typing import Optional

import hydra
import numpy as np
from matplotlib import pyplot as plt
from omegaconf import DictConfig

from abses.cells import PatchCell, raster_attribute
from abses.exp.experiment import Experiment
from abses.main import MainModel
from abses.nature import PatchModule
from abses.sequences import ActorsList


class Tree(PatchCell):
    """
    Breed `Tree` is a subclass of `PatchCell`.
    It has four different states:
    0: empty, i.e., no tree is located on the patch.
    1: has an intact tree.
    2: the tree here is burning now.
    3: the three here is burned and now scorched -cannot be burned again.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._state = 0

    def burning(self):
        """If the tree is burning, it ignites the neighboring trees."""
        if self._state == 2:
            neighbors = self.neighboring(moore=False, radius=1)
            # apply to all neighboring patches: trigger ignite method
            neighbors.select({"state": 1}).trigger("ignite")
            # after then, it becomes scorched and cannot be burned again.
            self._state = 3

    def grow(self) -> None:
        """Grows the tree here."""
        self._state = 1

    def ignite(self) -> None:
        """Ignite this tree."""
        if self._state == 1:
            self._state = 2

    @raster_attribute
    def state(self) -> int:
        """Return the state code."""
        return self._state


class Forest(MainModel):
    """
    Forest model where fire
    """

    def setup(self) -> None:
        # setup a grid space.
        grid: PatchModule = self.nature.create_module(
            how="from_resolution",
            name="forest",
            shape=self.params.shape,
            cell_cls=Tree,
            major_layer=True,
        )
        # random choose some patches to setup trees
        chosen_patches = grid.random.choice(self.num_trees, replace=False)
        # create trees on the selected patches.
        chosen_patches.trigger("grow")
        # ignite the trees in the leftmost column.
        ActorsList(self, grid.array_cells[:, 0]).trigger("ignite")

    def step(self):
        for tree in self.nature.forest:
            tree.burning()

    @property
    def burned_rate(self) -> float:
        """The burned trees in ratio."""
        state = self.nature.get_raster("state")
        return np.squeeze(state == 3).sum() / self.num_trees

    @property
    def num_trees(self) -> int:
        """Number of trees"""
        shape = self.params.shape
        return int(shape[0] * shape[1] * self.params.density)

    def plot_state(self):
        """Plot the state of trees."""
        categories = {
            0: "black",
            1: "green",
            2: "orange",
            3: "red",
        }
        cmap = plt.cm.colors.ListedColormap(
            [categories[i] for i in sorted(categories)]
        )
        data = self.nature.get_xarray("state")
        data.plot(cmap=cmap)
        plt.show()


@hydra.main(version_base=None, config_path="", config_name="config")
def main(cfg: Optional[DictConfig] = None):
    """运行模型"""
    exp = Experiment(model_cls=Forest)
    exp.batch_run(cfg=cfg)


if __name__ == "__main__":
    main()
    Experiment.summary(save=True)
