import types
from functools import partial
from operator import attrgetter

from loguru import logger
from mesa import datacollection

from abses.components import _Component
from abses.main import MainModel


class DataCollector(_Component, datacollection.DataCollector):
    """
    DataCollector is a wrap of mesa.datacollection.DataCollector class.
    This class inherits most functionality from its parent, mainly on data representation, but it
    demands slight changes to account for the differences in the ABSESpy API.

    Mesa's DataCollector class collects data at the model level and at the agent level. It also
    allows the user to define custom tables with data arising from the model. The data collected
    is stored in a dictionary of model variables and agent variables.
    """

    def __init__(self, model: MainModel, **kwargs):
        _Component.__init__(self, model=model, name="datacollector")
        datacollection.DataCollector.__init__(self, **kwargs)
        logger.info("DataCollector component initialized.")
        logger.debug(f"DataCollector initialized with {kwargs}.")

        self._model: MainModel = model

    def _record_agents(self, model):
        rep_funcs = self.agent_reporters.values()
        if all(hasattr(rep, "attribute_name") for rep in rep_funcs):
            prefix = ["model.time.tick", "unique_id"]
            attributes = [func.attribute_name for func in rep_funcs]
            get_reports = attrgetter(*prefix + attributes)

        else:

            def get_reports(actor):
                _prefix = (actor.model.time.tick, actor.unique_id)
                reports = tuple(rep(actor) for rep in rep_funcs)
                return _prefix + reports

        agent_records = map(get_reports, model.actors)
        return agent_records

    def collect(self):
        """Collect all the data for the given model object."""
        if self.model_reporters:
            for var, reporter in self.model_reporters.items():
                # Check if Lambda operator
                if isinstance(reporter, (types.LambdaType, partial)):
                    self.model_vars[var].append(reporter(self._model))
                elif isinstance(reporter, list):
                    self.model_vars[var].append(reporter[0](*reporter[1]))
                elif isinstance(reporter, str):
                    self.model_vars[var].append(reporter)
                else:
                    self.model_vars[var].append(reporter())

        if self.agent_reporters:
            agent_records = self._record_agents(self._model)
            self._agent_records[self._model.time.tick] = list(agent_records)
