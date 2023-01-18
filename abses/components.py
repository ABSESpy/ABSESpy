#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from abc import abstractmethod
from typing import Iterable, List, Optional, Set, Union

from agentpy.tools import AttrDict

from .bases import Mediator
from .log import Log
from .tools.func import iter_func, make_list

STATES = {
    -1: "Waiting",
    0: "new",
    1: "init",
    2: "ready",
    3: "complete",
}


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
    def _parsing_args(self) -> None:
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
    def parsing_params(self, params: dict) -> dict:
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
        self._parsing_args()
        # solving parameters diversely
        self._after_parsing()
        # handle parameters defined by users
        self.handle_params()
        return params

    def report_parameters(
        self, params: Optional[dict] = None, as_string: Optional[bool] = False
    ) -> Union[dict, str]:
        # TODO: show parameter table.
        if len(params) == 0:
            return None
        if as_string:
            return str(list(params.keys()))
        else:
            return params.keys()

    @abstractmethod
    def _after_parsing(self):
        pass

    @abstractmethod
    def handle_params(self):
        """
        Handle parameters after loading.
        """
        pass

    @abstractmethod
    def initialize(self):
        """
        Initialization after handle parameters.
        """
        pass


class MainComponent(Component):
    _states = STATES

    def __init__(self, name: Optional[str] = None):
        Component.__init__(self, name=name)
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

    def parsing_params(self, params: dict) -> dict:
        unsolved = super().parsing_params(params)
        finished = self.mediator.transfer_parsing(self, params)
        if finished:
            parameters = self.report_parameters(unsolved, as_string=True)
            message = f"Unsolved parameters: {parameters}."
            self.mediator.logging(
                message, condition=len(unsolved) > 0, level="warning"
            )
        return unsolved

    @iter_func("modules")
    def _after_parsing(self):
        pass
