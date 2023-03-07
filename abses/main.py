#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

import logging
from collections import namedtuple
from typing import (
    Dict,
    Iterable,
    NamedTuple,
    Optional,
    Tuple,
    TypeAlias,
    Union,
)

from agentpy import AttrDict, Model

from abses import __version__
from abses.tools.read_files import read_yaml

from .actor import Actor
from .bases import Mediator, Notice
from .components import STATES, MainComponent
from .container import AgentsContainer
from .human import BaseHuman
from .log import Log
from .nature import BaseNature
from .project import Folder
from .sequences import ActorsList
from .time import TimeDriver
from .tools.func import iter_func, make_list
from .variable import VariablesRegistry

logger = logging.getLogger(__name__)
LENGTH = 40  # session fill


class MainModel(Folder, MainComponent, Model, Notice):
    def __init__(
        self,
        name: Optional[str] = None,
        base: Optional[str] = None,
        parameters: Optional[Dict[str, any]] = None,
        human_class: Optional[BaseHuman] = None,
        nature_class: Optional[BaseNature] = None,
        settings_file: Optional[str] = None,
        _run_id: Optional[Tuple[int, int]] = None,
        **kwargs,
    ) -> None:
        Model.__init__(self, _run_id=_run_id)
        MainComponent.__init__(self, name=name)
        Folder.__init__(self, base=base)
        Notice.__init__(self)

        if nature_class is None:
            nature_class = BaseNature
        if human_class is None:
            human_class = BaseHuman
        if parameters is None:
            parameters = {}

        self.__version__: str = __version__
        self._human: BaseHuman = human_class(self)
        self._nature: BaseNature = nature_class(self)
        self._agents = AgentsContainer(model=self)
        # parameters
        # priority: init parameters > input parameters > settings_file
        self._init_params: AttrDict = AttrDict()
        self._init_params.update(parameters)
        self._init_params.update(kwargs)

        if settings_file is None:
            settings_file = parameters.pop("settings_file", None)
        self._settings_file: Optional[str] = settings_file
        # setup mediator
        self._time = TimeDriver(model=self, settings=self.settings.get("time"))
        self._db = self.settings.get("db", AttrDict())
        self.mediator = MainMediator(
            model=self, human=self.human, nature=self.nature
        )
        self._registry = VariablesRegistry(model=self)

    # ----------------------------------------------------------------
    def __repr__(self):
        name = self.__class__.__name__
        version = self.__version__
        return f"<{name}-{version}({self.name}): {self.state}>"

    # ----------------------------------------------------------------
    @property
    def agents(self) -> AgentsContainer:
        return self._agents

    @property
    def all_agents(self) -> ActorsList:
        return self.agents.to_list()

    @property
    def human(self) -> BaseHuman:
        return self._human

    @property
    def nature(self) -> BaseNature:
        return self._nature

    @property
    def registry(self) -> VariablesRegistry:
        return self._registry

    @property
    def time(self) -> TimeDriver:
        return self._time

    @property
    def db(self) -> AttrDict:
        return self._db

    @property
    def _settings_from_file(self) -> Dict[str, any]:
        # settings yaml as basic
        settings = AttrDict()
        if self._settings_file is not None:
            settings = read_yaml(self._settings_file, nesting=True)
        return settings

    @property
    def settings(self) -> Dict[str, any]:
        settings = AttrDict()
        # read basic settings file
        settings.update(self._settings_from_file)
        # input settings
        settings.update(self._init_params)
        return settings

    @iter_func("observers")
    def _when_time_go(self):
        pass

    def time_go(self, steps: int = 1) -> TimeDriver:
        for _ in range(steps):
            self.time.update()
            self._when_time_go()
            self.t += 1
            self.step()
            self.update()
        return self.time

    def sim_step(self):
        """Proceeds the simulation by one step, incrementing `Model.t` by 1
        and then calling :func:`Model.step` and :func:`Model.update`."""
        self.time_go()
        if self.t >= self._steps:
            self.running = False


Sender: TypeAlias = Union[MainComponent, Actor]
TypingUsers: TypeAlias = NamedTuple(
    "Users",
    [("human", BaseHuman), ("nature", BaseNature), ("model", MainModel)],
)
TypingResults: TypeAlias = NamedTuple(
    "Users", [("human", any), ("nature", any), ("model", any)]
)
USERS: Tuple[str] = ("model", "human", "nature")
Users: TypingUsers = namedtuple("Users", USERS)


class MainMediator(Mediator, Log):
    def __init__(self, model: MainModel, human: BaseHuman, nature: BaseNature):
        self.model: MainModel = model
        self.human: BaseHuman = human
        self.nature: BaseNature = nature
        model.mediator: MainMediator = self
        human.mediator: MainMediator = self
        nature.mediator: MainMediator = self
        self.users: TypingUsers = Users(
            model=model, human=human, nature=nature
        )
        self.sender: Optional[Sender] = None
        name = ", ".join([user.name for user in self.users])
        Log.__init__(self, name=name)
        self._change_state(0)  # state -> new: initialize all

    def __repr__(self) -> str:
        return f"<Mediator of: {self.name}>"

    def _change_state(self, state_code: int) -> bool:
        f"""
        Change all users' state to the assigned state.

        Args:
            state_code (int): {STATES}.

        Raises:
            ValueError: Invalid state code.
        """
        if state_code not in STATES:
            raise ValueError(
                f"Invalid state code {state_code}, valid: {STATES}"
            )
        for user in self.users:
            user.state = state_code
        return self._states_are(STATES[state_code])

    def _check_sender(self, sender: Sender) -> Dict[Sender, bool]:
        """
        Check the type of sender, save it as a string attribute.
        An available pattern includes:
            1. 'agent': any instance of 'Actor'.
            2. 'model': the bound instance of 'MainModel'.
            3. 'human': the bound instance of 'BaseHuman'.
            4. 'nature': the bound instance of 'BaseNature'.

        Args:
            sender (Sender): the sending request object.
        """
        if sender is self.model:
            self.sender = "model"
        elif sender is self.human:
            self.sender = "human"
        elif sender is self.nature:
            self.sender = "nature"
        elif isinstance(sender, Actor):
            self.sender = "agent"
        else:
            raise TypeError(f"Type of sender '{type(sender)}' is invalid.")

    def sender_matches(self, *args: str) -> bool:
        """
        Check if the sender now matches ANY given pattern.
        An available pattern includes:
            1. 'agent': any instance of 'Actor'.
            2. 'model': the bound instance of 'MainModel'.
            3. 'human': the bound instance of 'BaseHuman'.
            4. 'nature': the bound instance of 'BaseNature'.

        Returns:
            bool: if the 'self.sender' matches any input pattern, returns True.
        """
        is_matched = [self.sender == arg for arg in args]
        return any(is_matched)

    def session(self, msg: str, sep: str = ".", new_line: int = 0) -> str:
        """
        Wrap a session message.

        Args:
            msg (str): user's msg to wrap.
            sep (str, optional): separator. Defaults to ".".
            new_line (int, optional): how many new lines '\n' after wrapped message. Defaults to 0.

        Returns:
            str: a wrapped message.
        """
        wrapped_msg = " [%s] ".center(LENGTH, sep) % msg + "\n" * new_line
        self.logger.info(wrapped_msg)
        return wrapped_msg

    def _states_are(self, state: str, how: str = "all") -> bool:
        f"""
        Check users' states are same as the given state.

        Args:
            state (str): checking states {STATES}:
            how (str, optional):
                if 'all', returns True only if all users' state are checked.
                if 'any', any user's state checked, returns True.
                Defaults to 'all'.

        Raises:
            ValueError: Invalid input args.

        Returns:
            bool: if the check is successful.
        """
        states = [user.state == state for user in self.users]
        if how == "all":
            return all(states)
        elif how == "any":
            return any(states)
        else:
            raise ValueError(f"{how} in invalid, choose 'any' or 'all'.")

    def trigger_functions(
        self, users: Union[str, Iterable[str]], func_name: str, *args, **kwargs
    ) -> TypingResults:
        f"""
        Trigger functions for all users

        Args:
            users (Union[str, Iterable[str]]): which users to trigger, choose one or more from {USERS}.
            func_name (str): name of the function to trigger.
            *args, **kwargs: additional arguments to pass to the func.

        Returns:
            results (NamedTuple[({USERS}), Optional[any]]): a named tuple where each user in {USERS} storing their results.
        """
        results = {}
        for user in USERS:
            if user not in make_list(users):
                results[user] = None
                continue
            obj = self.users.__getattribute__(user)
            func = obj.__getattribute__(func_name)
            results[user] = func(*args, **kwargs)
        return Users(**results)

    def logging(self, message, condition: bool = True, level="warning"):
        logging = getattr(self.logger, level)
        if condition:
            logging(message)

    def transfer_parsing(self, sender: Sender, params: Dict[str, any]) -> bool:
        f"""
        Transfer parameters parsing.

        Args:
            sender (Sender): any component from {USERS}.
            params (AttrDict): dictionary of parameters to parse.

        Returns:
            bool: parsing parameters finished if all model, human, nature components finished, returns True, else False.
        """
        self._check_sender(sender)
        all_finished = False
        # MainModel parsing parameters finished, trigger others.
        if self.sender_matches("model"):
            self.model.p.update(
                self.model.params
            )  # todo remove this if self.p is removed
            self.human.parsing_params(params)
            self.nature.parsing_params(params)
            return all_finished
        # Human / Nature parsing parameters finished, report.
        elif self.sender_matches("human", "nature"):
            sender.state = 1
            self.logger.info(f"{sender.name} parsed parameters.")
            # finished parsing parameters, change state to initialized.
            if self._states_are("init", how="all"):
                self.logger.info("All parameters are initialized.")
                all_finished = True
            return all_finished

    def _new(self):
        if self.sender_matches("model"):
            # TODO run id
            run_id = self.model._run_id
            if run_id is not None:
                run_id = run_id[0]
            self.session(f"Model {self.model.name} ID-{run_id}", sep="*")
        if self._states_are("new"):
            # Automatically parsing parameters
            self.model.state = 1

    def _init(self):
        if self.sender_matches("model"):
            self.session("Parsing parameters")
            self.model.parsing_params(self.model.settings)
            self.model.initialize()
            self.nature.initialize()
            self.human.initialize()
            self.session("Initialized")

    def _ready(self):
        if self.sender_matches("model"):
            self.session("Ready for simulation")

    def _complete(self):
        if self.sender_matches("model"):
            self.session(f"Completed in {self.model.t} steps", new_line=0)
            self.session("Finished", sep="*", new_line=1)
            self.human.state = 3
            self.nature.state = 3
        if self.sender_matches("human"):
            self.human.report_vars()
        if self.sender_matches("nature"):
            self.nature.report_vars()

    def transfer_event(
        self, sender: object, event: str, *args, **kwargs
    ) -> None:
        self._check_sender(sender)
        event_func = self.__getattribute__(f"_{event}")
        return event_func(*args, **kwargs)

    def transfer_request(self, sender: object, attr: str, **kwargs) -> object:
        self._check_sender(sender)
        return (
            self.nature.get_patch(attr, **kwargs)
            if self.sender_matches("agent", "human")
            else None
        )
