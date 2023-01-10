#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from .agents import BaseAgent
from .log import Log

LENGTH = 40  # session fill


class MainMediator(Log):
    def __init__(self, model, human, nature):
        Log.__init__(self, name="Mediator")
        self._model = model
        self._human = human
        self._nature = nature
        model._mediator = self
        human._mediator = self
        nature._mediator = self
        self.sender = None
        self._set_state(0)

    def __repr__(self):
        return "<Model-Mediator>"

    def _set_state(self, state_code: int):
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
            self.model._initialize()
            self.nature._initialize_all()
            self.human._initialize_all()
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
