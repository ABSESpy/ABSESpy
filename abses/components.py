#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from abc import abstractmethod
from typing import Iterable, List, Optional

from agentpy.tools import AttrDict

from .log import Log
from .mediator import MainMediator
from .tools.func import make_list
from .tools.read_files import parse_yaml


def broadcast(func):
    """
    A decorator broadcasting MainComponent function to Component if available.

    Args:
        func (callable): function bound in a Component Object.
    """

    def broadcast_func(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if not hasattr(self, "modules"):
            return result
        for module in getattr(self, "modules"):
            getattr(module, func.__name__)(*args, **kwargs)
        return result

    return broadcast_func


class Component(Log):
    """
    The Base Component provides the basic functionality of storing a mediator's
    instance inside component objects.
    """

    def __init__(self, name: Optional[str] = None):
        if name is None:
            name = self.__class__.__name__.lower()
        Log.__init__(self, name)
        self._arguments: List[str] = []
        self._name: str = name
        self._parameters: dict = AttrDict()

    @property
    def name(self) -> str:
        return self._name

    @property
    def params(self) -> dict:
        return self._parameters

    @params.setter
    def params(self, my_params: dict) -> None:
        self.params.update(my_params)

    @property
    def arguments(self) -> List[str]:
        return self._arguments

    @arguments.setter
    def arguments(self, args: "str|Iterable[str]") -> None:
        arg_lst = make_list(args)
        self._arguments.extend(arg_lst)

    def parse_yaml_path(self, path: Optional[str]) -> dict:
        if path is None:
            return dict()
        else:
            return parse_yaml(path, nesting=True)

    def init_arguments(self) -> None:
        arguments = getattr(self.__class__, "args", [])
        for arg in arguments:
            self.arguments = arg
            value = self.params[arg]
            setattr(self, arg, value)

    @broadcast
    def close_log(self):
        super().close_log()

    def _parsing_args(self, params):
        self.init_arguments()
        for arg in self.arguments:
            if arg in params:
                self.params[arg] = params.pop(arg)
            # else:
            # self.logger.warning(f"Expected argument {arg} is not in params.")

    @broadcast
    def _parsing_params(self, params):
        # select my params
        self.params = params.pop(self.name, {})
        # parsing arguments
        self._parsing_args(params)
        # retrieve specific parameters and update
        for key in list(params.keys()):
            if key in self.params:
                self.params[key] = params.pop(key)
                self.logger.debug(f"Parameter [{key}] updated.")
        # handle parameters
        self.handle_params()
        return params

    @abstractmethod
    def handle_params(self):
        pass

    @abstractmethod
    def _initialize(self, *args, **kwargs):
        pass


class MainComponent(Component):
    VALID_STATE = {
        -1: "Waiting",
        0: "new",
        1: "init",
        2: "ready",
        3: "complete",
    }

    def __init__(self, *args, **kwargs):
        Component.__init__(self, *args, **kwargs)
        self._state = -1  # init state waiting

    @property
    def mediator(self) -> MainMediator:
        return self._mediator

    @mediator.setter
    def mediator(self, mediator) -> None:
        self._mediator = mediator

    @property
    def state(self) -> str:
        return self.VALID_STATE[self._state]

    @state.setter
    def state(self, code):
        if code not in self.VALID_STATE:
            raise ValueError(
                f"Invalid state {code}, valid: {self.VALID_STATE}."
            )
        elif code == self._state:
            self.logger.warning(f"STATE set repeated: {self.state}!")
        elif code < self._state:
            self.logger.critical(
                f"Fallback state: setting {self.VALID_STATE[code]} to {self.state}"
            )
        else:
            self._state = code
        self.mediator.transfer_event(sender=self, event=self.state)

    def _parsing_params(self, params: dict):
        self.mediator.transfer_parsing(self, params)
        return super()._parsing_params(params)
