from operator import attrgetter

from mesa import datacollection

from abses.components import _Component
from abses.main import MainModel


class DataCollector(_Component, datacollection.DataCollector):
    def __init__(self, model: MainModel, **kwargs):
        _Component.__init__(self, model=model, name="datacollector")
        datacollection.DataCollector.__init__(self, **kwargs)
        self._model: MainModel = model

    def _record_agents(self, model):
        rep_funcs = self.agent_reporters.values()
        if all([hasattr(rep, "attribute_name") for rep in rep_funcs]):
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
        if self.agent_reporters:
            agent_records = self._record_agents(self._model)
            self._agent_records[self._model.time.tick] = list(agent_records)

        else:
            pass
