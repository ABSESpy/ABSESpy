#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import networkx as nx

from .modules import CompositeModule, Module


class HumanModule(Module):
    def __init__(self, model, name=None):
        super().__init__(model, name)
        pass

    pass


class BaseHuman(CompositeModule, HumanModule):
    def __init__(self, model, name="human"):
        HumanModule.__init__(self, model, name)
        CompositeModule.__init__(self, model, name=name)

    def require(self, attr: str) -> object:
        return self.mediator.transfer_require(self, attr)


#     def mock(self, agents, attrs, how="attr"):
#         tutors = self.to_agents(agents.tutor.now)
#         for attr in make_list(attrs):
#             values = tutors.array(attr, how)
#             agents.update(attr, values)


# def skip_if_close(func):
#     def skip_module_method(self, *args, **kwargs):
#         if self.opening:
#             func(self, *args, **kwargs)
#         else:
#             if self.log_flag:
#                 self.logger.warning(f"{self}.")

#     return skip_module_method
