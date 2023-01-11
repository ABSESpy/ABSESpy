#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

import logging

from agentpy import Model

from abses import __version__
from abses.tools.read_files import read_yaml

from .components import MainComponent
from .container import AgentsContainer
from .human import BaseHuman
from .log import Log
from .nature import BaseNature
from .objects import BaseAgent, Mediator, Notice
from .project import Folder

logger = logging.getLogger(__name__)
LENGTH = 40  # session fill


class MainModel(Folder, MainComponent, Model, Notice):
    def __init__(
        self,
        parameters: dict = None,
        name: str = None,
        base: str = None,
        human_class: BaseHuman = None,
        nature_class: BaseNature = None,
        settings_file: str = None,
        _run_id=None,
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

        self.__version__ = __version__
        self._human = human_class(self)
        self._nature = nature_class(self)
        self._agents = AgentsContainer(self)
        # parameters
        # priority: init parameters > input parameters > settings_file
        self._init_params = {}
        self._init_params.update(parameters)
        self._init_params.update(kwargs)
        if settings_file is None:
            settings_file = parameters.get("settings_file", None)
        self._settings_file = settings_file
        # setup mediator
        self.mediator = MainMediator(
            model=self, human=self.human, nature=self.nature
        )

    def __repr__(self):
        name = self.__class__.__name__
        version = self.__version__
        return f"{name}-{version}({self.name}): {self.state}"

    @property
    def agents(self) -> AgentsContainer:
        return self._agents

    @property
    def human(self) -> BaseHuman:
        return self._human

    @property
    def nature(self) -> BaseNature:
        return self._nature

    @property
    def settings_file(self) -> dict:
        # settings yaml as basic
        settings = dict()
        if self._settings_file is not None:
            settings = read_yaml(self._settings_file, nesting=True)
        return settings

    @property
    def settings(self) -> dict:
        settings = dict()
        # read basic settings file
        settings.update(self.settings_file)
        # input settings
        settings.update(self._init_params)
        return settings

    def initialize(self):
        unsolved = self._parsing_params(self.settings)
        if len(unsolved.keys()) > 0:
            self.logger.warning(f"Unsolved parameters: {unsolved.keys()}.")
        self.p.update(self.params)

    # TODO remove this
    def close_log(self):
        super().close_log()
        self.nature.close_log()
        self.human.close_log()


class MainMediator(Mediator, Log):
    def __init__(self, model, human, nature):
        Log.__init__(self, name="Mediator")
        self._model: MainModel = model
        self._human: BaseHuman = human
        self._nature: BaseNature = nature
        model.mediator: MainMediator = self
        human.mediator: MainMediator = self
        nature.mediator: MainMediator = self
        self.sender: any = None
        self._change_state(0)

    def __repr__(self):
        return "<Model-Mediator>"

    def _change_state(self, state_code: int):
        self.model.state = state_code
        self.human.state = state_code
        self.nature.state = state_code

    @property
    def model(self):
        return self._model

    @property
    def nature(self):
        return self._nature

    @property
    def human(self):
        return self._human

    def _check_sender(self, sender: object) -> dict:
        is_model = sender is self.model
        is_human = sender is self.human
        is_nature = sender is self.nature
        is_agent = isinstance(sender, BaseAgent)
        self.sender = {
            "model": is_model,
            "human": is_human,
            "nature": is_nature,
            "agent": is_agent,
        }

    def _sender_matches(self, *args) -> bool:
        is_matched = [self.sender[p] for p in args]
        return any(is_matched)

    def new_session(self, msg: str, sep: str = ".", new_line=0):
        self.logger.info(" [%s] ".center(LENGTH, sep) % msg + "\n" * new_line)

    def _check_state(self, state: str):
        model_is = self.model.state == state
        nature_is = self.nature.state == state
        human_is = self.human.state == state
        return model_is, nature_is, human_is

    def _all_state_is(self, state: str) -> bool:
        return all(self._check_state(state))

    def transfer_parsing(self, sender: object, value):
        if sender is self.model:
            self.human._parsing_params(value)
            self.nature._parsing_params(value)

    def new(self):
        if self._sender_matches("model"):
            run_id = self.model._run_id
            if run_id is not None:
                run_id = run_id[0]
            self.new_session(f"Model {self.model.name} ID-{run_id}", sep="*")
        elif self._sender_matches("human", "nature"):
            pass
        if self._all_state_is("new"):
            # Automatically parsing parameters
            self.model.state = 1

    def init(self):
        if self._sender_matches("model"):
            self.new_session("Parsing parameters")
            self.model.initialize()
            self.nature.initialize()
            self.human.initialize()
            self.new_session("Initialized")
        elif self._sender_matches("human", "nature"):
            pass

    def ready(self):
        if self._sender_matches("model"):
            self.new_session("Ready for simulation")

    def complete(self):
        if self._sender_matches("model"):
            self.new_session(f"Completed in {self.model.t} steps", new_line=0)
            self.new_session("Finished", sep="*", new_line=1)
            self.human.state = 3
            self.nature.state = 3
        if self._sender_matches("human"):
            self.human.report_vars()
        if self._sender_matches("nature"):
            self.nature.report_vars()

    def transfer_event(self, sender: object, event: str, *args) -> None:
        self._check_sender(sender)
        event_func = self.__getattribute__(event)
        event_func(*args)

    def transfer_require(self, sender: object, attr: str, **kwargs) -> object:
        if sender is self.human or isinstance(sender, BaseAgent):
            patch_obj = self.nature.send_patch(attr, **kwargs)
            return patch_obj
