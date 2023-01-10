#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import logging

from agentpy import Model

from abses import __version__

from .base_human import BaseHuman
from .base_nature import BaseNature
from .components import MainComponent
from .container import AgentsContainer
from .mediator import MainMediator
from .objects import Notice
from .project import Folder

logger = logging.getLogger(__name__)


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
        self.arguments = ["steps", "settings_file"]

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
        cls_name = self.__class__.__name__
        return f"{cls_name}-{self.__version__}({self.name}): {self.state}"

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
    def settings_file(self) -> str:
        return self._settings_file

    def _initialize(self):
        # read settings file
        settings = self.parse_yaml_path(self.settings_file)
        # settings yaml as basic, update if any input when init
        settings.update(self._init_params)
        unsolved = self._parsing_params(settings)
        if len(unsolved.keys()) > 0:
            self.logger.warning(f"Unsolved parameters: {unsolved.keys()}.")
        self.p.update(self.params)

    def close_log(self):
        super().close_log()
        self.nature.close_log()
        self.human.close_log()
