#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import pytest

from abses.states import States


# Tests
def test_status_initial_state():
    status = States()
    assert status.state == "new"


def test_status_state_property():
    status = States()
    status.set_state(1)
    assert status.state == "init"


def test_status_invalid_state_setting():
    status = States()
    with pytest.raises(ValueError, match="Invalid state 4, valid: .*!"):
        status.set_state(4)


def test_status_repeat_state_setting():
    status = States()
    status.set_state(1)
    with pytest.raises(ValueError, match="Setting state repeat: init!"):
        status.set_state(1)


def test_status_retreat_state_setting():
    status = States()
    status.set_state(3)
    with pytest.raises(
        ValueError, match="State cannot retreat from complete to ready!"
    ):
        status.set_state(2)
