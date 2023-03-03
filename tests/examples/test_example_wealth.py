#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/
import numpy as np

from abses import Actor, MainModel
from abses.actor import check_rule, link_to, perception


def gini(x):
    """Calculate Gini Coefficient"""
    # By Warren Weckesser https://stackoverflow.com/a/39513799

    x = np.array(x)
    mad = np.abs(np.subtract.outer(x, x)).mean()  # Mean absolute difference
    rmad = mad / np.mean(x)  # Relative mean absolute difference
    return 0.5 * rmad


class WealthyActor(Actor):

    """Demo model of wealth transferring."""

    def setup(self):
        self.wealth: int = 1
        self.rule(
            when={"fit_in": False},
            then="move",
            check_now=False,
            frequency="now",
        )

    # setup property 'potential partner',
    # which auto links to these potential partners.
    @link_to
    def potential_partners(self):
        return self.neighbors(distance=3, approach=8)

    @perception
    def fit_in(self) -> bool:
        return len(self.potential_partners) != 0

    @check_rule(loop=True)
    def wealth_transfer(self):
        partner = self.potential_partners.random_choose()
        if self.wealth > 0:
            partner.wealth += 1
            self.wealth -= 1


class WealthModel(MainModel):

    """A simple model of random wealth transfers"""

    def setup(self):
        actors = self.agents.create(WealthyActor, 10)
        self.nature.add_agents(actors, replace=True)

    def step(self):
        self.all_agents.wealth_transfer()

    def update(self):
        self.record("Gini Coefficient", gini(self.all_agents.wealth))

    def end(self):
        self.all_agents.record("wealth")


def test_model_run():
    parameters = {
        "wealth demo": {
            "steps": 10,
            "seed": 42,
        }
    }

    model = WealthModel(
        name="wealth demo", base="tests", parameters=parameters
    )
    # assert not actor.fit_in
    results = model.run()
    # TODO fixing double times record
    assert len(results.variables.WealthyActor) == len(model.agents) * 2
