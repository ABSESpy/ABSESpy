#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import pytest

from abses.actor import Actor, ActorsList
from abses.main import MainModel


class MockAgent(Actor):
    pass


@pytest.fixture
def actor():
    return Actor(MainModel())


@pytest.fixture
def other_agent():
    return MockAgent(MainModel())


def test_links_property(actor):
    assert isinstance(actor.links, list)
    assert len(actor.links) == 0


def test_lands_property(actor):
    assert isinstance(actor.lands, list)
    assert len(actor.lands) == 0


def test_link_to_actor(actor, other_agent):
    actor.link_to(other_agent, link="friends")
    assert "friends" in actor.links
    assert other_agent in actor._links["friends"]


def test_link_to_invalid_agent(actor):
    with pytest.raises(TypeError):
        actor.link_to("invalid_agent")


def test_linked_agents(actor, other_agent):
    actor.link_to(other_agent, link="friends")
    linked = actor.linked_agents("friends")
    assert isinstance(
        linked, ActorsList
    )  # Assuming ActorsList is the expected return type
    assert other_agent in linked


def test_linked_agents_with_invalid_link(actor):
    with pytest.raises(KeyError):
        actor.linked_agents("invalid_link")
