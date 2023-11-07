#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from typing import Iterable

import pytest

from abses import Actor
from abses.actor import perception
from abses.decision import Decision, response
from abses.main import MainModel


class OverWorking(Decision):
    """内卷策略"""

    __strategies__ = {
        True: "Decide to work longer.",
        False: "No longer work more...",
    }


class InvolutingActor(Actor):
    """A poor guy who has to work harder..."""

    __decisions__ = OverWorking

    def __init__(self, *args, working_hrs: float = 7.0, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.working_hrs = working_hrs
        self.overwork = False

    @perception(nodata=False)
    def avg_working_hrs(self) -> float:
        """The average wealth of acquaintances."""
        acquaintance = self.linked("colleague")
        return acquaintance.array("working_hrs").mean()

    @response(decision="over_working", strategy=True)
    def work_harder(self):
        """Work harder."""
        self.working_hrs += 1

    @OverWorking.making
    def feel_peer_pressure(self):
        """Feel stressful when others work harder than self."""
        return self.working_hrs <= self.avg_working_hrs()


def test_load_decisions():
    """测试能够顺利加载decision"""
    strategies = {"C": "cooperate", "D": "defect"}

    class TestDecision(Decision):
        """Testing load decisions"""

        __strategies__ = strategies

    decision = TestDecision()
    assert strategies == decision.strategies
    assert decision.has_strategy("C")
    assert decision.name == "test_decision"

    with pytest.raises(TypeError):

        class BadDecision(Decision):
            """Testing load decisions"""

            __strategies__ = "Bad testing (not dictionary)."

        decision = BadDecision()


@pytest.fixture(name="agents")
def setup_agents():
    """Setup three poor guys for involution tests."""
    model = MainModel()
    agents: Iterable[InvolutingActor] = model.agents.create(InvolutingActor, 3)
    agent1, agent2, agent3 = agents

    agent1.working_hrs = 7
    agent2.working_hrs = 8
    agent3.working_hrs = 9

    agent1.link_to(agent2, "colleague")
    agent1.link_to(agent3, "colleague")
    return agent1, agent2, agent3


def test_working_harder(agents: Iterable[InvolutingActor]):
    """Test agents will work harder and harder..."""
    agent1, agent2, agent3 = agents
    assert agent2 in agent1.linked("colleague")
    assert agent3 in agent1.linked("colleague")

    assert agent1.avg_working_hrs() == (8 + 9) / 2
    assert agent1.feel_peer_pressure

    agent1.work_harder()
    assert agent1.working_hrs == 8.0

    # agent1.decisions.making()
    # assert agent1.working_hrs == 9.0
    # assert agent1.d.overworking
