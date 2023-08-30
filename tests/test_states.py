#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from unittest.mock import Mock

import pytest

from abses.states import States


# Assuming Mediator is from an external module, mock it for simplicity in this demonstration
class Mediator:
    def transfer_event(self, sender, event):
        pass


# Your STATES dictionary and Status class remains as is ...


# Tests
def test_status_initial_state():
    status = States()
    assert status.state == "Waiting"


def test_status_state_property():
    status = States()
    status._state = 1
    assert status.state == "init"


def test_status_invalid_state_setting():
    status = States()
    with pytest.raises(ValueError, match="Invalid state 4, valid: .*!"):
        status.state = 4


def test_status_repeat_state_setting():
    status = States()
    status._state = 1
    with pytest.raises(ValueError, match="Setting state repeat: init!"):
        status.state = 1


def test_status_retreat_state_setting():
    status = States()
    status._state = 3
    with pytest.raises(
        ValueError, match="State cannot retreat from init to complete!"
    ):
        status.state = 1


def test_status_valid_state_transfer_event_call():
    status = States()
    status.mediator = Mock()
    status.state = 1
    status.mediator.transfer_event.assert_called_once_with(
        sender=status, event="init"
    )
