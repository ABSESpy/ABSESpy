#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

STATES = {
    0: "new",
    1: "init",
    2: "ready",
    3: "complete",
}


class _States:
    """
    模型的主要部分（自然模块和人类模块），动作将发送给 Mediator 进行记录
    """

    _states = STATES

    def __init__(self) -> None:
        self._state: int = 0  # new model

    @property
    def state(self) -> str:
        """模块状态"""
        return self._states[self._state]

    def set_state(self, code: int) -> None:
        """设置模块状态"""
        if code not in self._states:
            raise ValueError(f"Invalid state {code}, valid: {self._states}!")
        if code == self._state:
            raise ValueError(f"Setting state repeat: {self.state}!")
        if code < self._state:
            raise ValueError(
                f"State cannot retreat from {self.state} to {self._states[code]}!"
            )
        self._state = code
