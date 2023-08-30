#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from abses.bases import Mediator

STATES = {
    -1: "Waiting",
    0: "new",
    1: "init",
    2: "ready",
    3: "complete",
}


class States:
    """
    模型的主要部分（自然模块和人类模块），动作将发送给 Mediator 进行记录
    """

    _states = STATES

    def __init__(self):
        self._state = -1  # init state waiting
        self._mediator = Mediator()

    @property
    def mediator(self) -> Mediator:
        """中介者"""
        return self._mediator

    @mediator.setter
    def mediator(self, mediator) -> None:
        self._mediator = mediator

    @property
    def state(self) -> str:
        """模块状态"""
        return self._states[self._state]

    @state.setter
    def state(self, code):
        if code not in self._states:
            raise ValueError(f"Invalid state {code}, valid: {self._states}!")
        if code == self._state:
            raise ValueError(f"Setting state repeat: {self.state}!")
        if code < self._state:
            raise ValueError(
                f"State cannot retreat from {self._states[code]} to {self.state}!"
            )
        self._state = code
        self.mediator.transfer_event(sender=self, event=self.state)
