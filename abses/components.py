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
from .objects import Mediator
from .tools.func import make_list

STATES = {
    -1: "Waiting",
    0: "new",
    1: "init",
    2: "ready",
    3: "complete",
}


def iter_func(elements: str) -> callable:
    """
    A decorator broadcasting function to all elements if available.

    elements:
        elements (str): attribute name where object store iterable elements.
        All element in this iterable object will call the decorated function.
    """

    def broadcast(func: callable) -> callable:
        def broadcast_func(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            if not hasattr(self, elements):
                return result
            for element in getattr(self, elements):
                getattr(element, func.__name__)(*args, **kwargs)
            return result

        return broadcast_func

    return broadcast


class Component(Log):
    """
    The Base Component provides the basic functionality of storing a mediator's
    instance inside component objects.
    """

    def __init__(self, name: Optional[str] = None):
        Log.__init__(self, name=name)
        self._arguments: List[str] = []
        self._parameters: dict = AttrDict()

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
        self._arguments = sorted(list(set(self.arguments)))

    @iter_func("modules")
    def _init_arguments(self) -> None:
        """
        Initialize arguments of the component then delete from param dictionary.

        Raises:
            KeyError: cannot find argument in parameters.
        """
        arguments = getattr(self.__class__, "args", [])
        self.arguments = arguments
        for arg in self.arguments:
            try:
                value = self.params[arg]
                self.__setattr__(arg, value)
                del self.params[arg]
            except KeyError:
                raise KeyError(f"arg '{arg}' not found in parameters.")

    @iter_func("modules")
    def _parsing_params(self, params: dict) -> dict:
        """
        Parsing parameters belongs to this component.

        Args:
            params (dict): input settings.

        Returns:
            dict: unsolved parameters.
        """
        # select my params
        self.params = params.pop(self.name, {})
        # retrieve specific parameters and update
        for key in list(params.keys()):
            if key in self.params:
                value = params.pop(key)
                self.logger.debug(
                    f"Using {value} to update {self.params[key]} for '{key}'"
                )
                self.params[key] = value
        # setup arguments
        self._init_arguments()
        # handle parameters
        self.handle_params()
        return params

    @abstractmethod
    def handle_params(self):
        """
        Handle parameters after loading.
        """
        pass

    @abstractmethod
    def initialize(self):
        pass


class MainComponent(Component):
    _states = STATES

    def __init__(self, *args, **kwargs):
        Component.__init__(self, *args, **kwargs)
        self._state = -1  # init state waiting
        self._mediator = Mediator()

    @property
    def mediator(self) -> Mediator:
        return self._mediator

    @mediator.setter
    def mediator(self, mediator) -> None:
        self._mediator = mediator

    @property
    def state(self) -> str:
        return self._states[self._state]

    @state.setter
    def state(self, code):
        if code not in self._states:
            raise ValueError(f"Invalid state {code}, valid: {self._states}!")
        elif code == self._state:
            raise ValueError(f"Setting state repeat: {self.state}!")
        elif code < self._state:
            raise ValueError(
                f"State cannot retreat from {self._states[code]} to {self.state}!"
            )
        else:
            self._state = code
        self.mediator.transfer_event(sender=self, event=self.state)

    def _parsing_params(self, params: dict):
        unsolved = super()._parsing_params(params)
        self.mediator.transfer_parsing(self, params)
        return unsolved

    # TODO: refactor this to log
    @iter_func("modules")
    def close_log(self):
        super().close_log()

    @iter_func("modules")
    def initialize(self):
        self.state = 1
