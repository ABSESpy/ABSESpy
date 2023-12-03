#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import numpy as np
import pytest

from abses import Actor, MainModel
from abses.datacollection import DataCollector

rng = np.random.default_rng(seed=42)


class MockAgent(Actor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.val = 0
        self.val2 = 2


class anotherMockAgent(MockAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.val3 = 3


class MockModel(MainModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_var = 100
        self.n = 10

        self.agents.create(MockAgent, self.n - 3)
        self.agents.create(anotherMockAgent, 3)

        self.datacollector = DataCollector(
            model=self,
            model_reporters={
                "const": "model_var",
                "pop_ratio": lambda m: len(m.agents["MockAgent"])
                / len(m.agents["anotherMockAgent"]),
            },
            agent_reporters={
                "const": "val2",
            },
        )

    def step(self):
        if self.time.tick == 5:
            self.agents.remove(self.actors[5])

        self.datacollector.collect()


class Test_DataCollector:
    def setup_method(self):
        self.model = MockModel(parameters={"time": {"end": 10}})

        self.model.run_model()

    def test_model_vars(self):
        datacollector = self.model.datacollector
        assert "const" in datacollector.model_vars
        assert "pop_ratio" in datacollector.model_vars
        ratio = 2.3333333333333335  # Implied ratio at beginning
        assert datacollector.model_vars["pop_ratio"][1] == ratio
        ratio = 2.0  # Implied ratio at end
        assert datacollector.model_vars["pop_ratio"][-1] == ratio

    def test_agent_records(self):
        pass

    def test_table_rows(self):
        pass


"""
""
Test the DataCollector
""
import unittest

from mesa import Agent, Model
from mesa.time import BaseScheduler


class MockAgent(Agent):
    ""
    Minimalistic agent for testing purposes.
    ""

    def __init__(self, unique_id, model, val=0):
        super().__init__(unique_id, model)
        self.val = val
        self.val2 = val

    def step(self):
        ""
        Increment vals by 1.
        ""
        self.val += 1
        self.val2 += 1

    def double_val(self):
        return self.val * 2

    def write_final_values(self):
        ""
        Write the final value to the appropriate table.
        ""
        row = {"agent_id": self.unique_id, "final_value": self.val}
        self.model.datacollector.add_table_row("Final_Values", row)


def agent_function_with_params(agent, multiplier, offset):
    return (agent.val * multiplier) + offset


class DifferentMockAgent(MockAgent):
    # We define a different MockAgent to test for attributes that are present
    # only in 1 type of agent, but not the other.
    def __init__(self, unique_id, model, val=0):
        super().__init__(unique_id, model, val=val)
        self.val3 = val + 42


class MockModel(Model):
    ""
    Minimalistic model for testing purposes.
    ""

    schedule = BaseScheduler(None)

    def __init__(self):
        self.schedule = BaseScheduler(self)
        self.model_val = 100

        self.n = 10
        for i in range(self.n):
            self.schedule.add(MockAgent(i, self, val=i))
        self.initialize_data_collector(
            model_reporters={
                "total_agents": lambda m: m.schedule.get_agent_count(),
                "model_value": "model_val",
                "model_calc": self.schedule.get_agent_count,
                "model_calc_comp": [self.test_model_calc_comp, [3, 4]],
                "model_calc_fail": [self.test_model_calc_comp, [12, 0]],
            },
            agent_reporters={
                "value": lambda a: a.val,
                "value2": "val2",
                "double_value": MockAgent.double_val,
                "value_with_params": [agent_function_with_params, [2, 3]],
            },
            tables={"Final_Values": ["agent_id", "final_value"]},
        )

    def test_model_calc_comp(self, input1, input2):
        if input2 > 0:
            return (self.model_val * input1) / input2
        else:
            assert ValueError
            return None

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)


class TestDataCollector(unittest.TestCase):
    def setUp(self):
        ""
        Create the model and run it a set number of steps.
        ""
        self.model = MockModel()
        for i in range(7):
            if i == 4:
                self.model.schedule.remove(self.model.schedule._agents[3])
            self.model.step()

        # Write to table:
        for agent in self.model.schedule.agents:
            agent.write_final_values()

    def step_assertion(self, model_var):
        for element in model_var:
            if model_var.index(element) < 4:
                assert element == 10
            else:
                assert element == 9

    def test_model_vars(self):
        ""
        Test model-level variable collection.
        ""
        data_collector = self.model.datacollector
        assert "total_agents" in data_collector.model_vars
        assert "model_value" in data_collector.model_vars
        assert "model_calc" in data_collector.model_vars
        assert "model_calc_comp" in data_collector.model_vars
        assert "model_calc_fail" in data_collector.model_vars
        length = 8
        assert len(data_collector.model_vars["total_agents"]) == length
        assert len(data_collector.model_vars["model_value"]) == length
        assert len(data_collector.model_vars["model_calc"]) == length
        assert len(data_collector.model_vars["model_calc_comp"]) == length
        self.step_assertion(data_collector.model_vars["total_agents"])
        for element in data_collector.model_vars["model_value"]:
            assert element == 100
        self.step_assertion(data_collector.model_vars["model_calc"])
        for element in data_collector.model_vars["model_calc_comp"]:
            assert element == 75
        for element in data_collector.model_vars["model_calc_fail"]:
            assert element is None

    def test_agent_records(self):
        ""
        Test agent-level variable collection.
        ""
        data_collector = self.model.datacollector
        agent_table = data_collector.get_agent_vars_dataframe()

        assert "double_value" in list(agent_table.columns)
        assert "value_with_params" in list(agent_table.columns)

        # Check the double_value column
        for (step, agent_id), value in agent_table["double_value"].items():
            expected_value = (step + agent_id) * 2
            self.assertEqual(value, expected_value)

        # Check the value_with_params column
        for (step, agent_id), value in agent_table["value_with_params"].items():
            expected_value = ((step + agent_id) * 2) + 3
            self.assertEqual(value, expected_value)

        assert len(data_collector._agent_records) == 8
        for step, records in data_collector._agent_records.items():
            if step < 5:
                assert len(records) == 10
            else:
                assert len(records) == 9

            for values in records:
                assert len(values) == 6

        assert "value" in list(agent_table.columns)
        assert "value2" in list(agent_table.columns)
        assert "value3" not in list(agent_table.columns)

        with self.assertRaises(KeyError):
            data_collector._agent_records[8]

    def test_table_rows(self):
        ""
        Test table collection
        ""
        data_collector = self.model.datacollector
        assert len(data_collector.tables["Final_Values"]) == 2
        assert "agent_id" in data_collector.tables["Final_Values"]
        assert "final_value" in data_collector.tables["Final_Values"]
        for _key, data in data_collector.tables["Final_Values"].items():
            assert len(data) == 9

        with self.assertRaises(Exception):
            data_collector.add_table_row("error_table", {})

        with self.assertRaises(Exception):
            data_collector.add_table_row("Final_Values", {"final_value": 10})

    def test_exports(self):
        ""
        Test DataFrame exports
        ""
        data_collector = self.model.datacollector
        model_vars = data_collector.get_model_vars_dataframe()
        agent_vars = data_collector.get_agent_vars_dataframe()
        table_df = data_collector.get_table_dataframe("Final_Values")
        assert model_vars.shape == (8, 5)
        assert agent_vars.shape == (77, 4)
        assert table_df.shape == (9, 2)

        with self.assertRaises(Exception):
            table_df = data_collector.get_table_dataframe("not a real table")


class TestDataCollectorInitialization(unittest.TestCase):
    def setUp(self):
        self.model = Model()

    def test_initialize_before_scheduler(self):
        with self.assertRaises(RuntimeError) as cm:
            self.model.initialize_data_collector()
        self.assertEqual(
            str(cm.exception),
            "You must initialize the scheduler (self.schedule) before initializing the data collector.",
        )

    def test_initialize_before_agents_added_to_scheduler(self):
        with self.assertRaises(RuntimeError) as cm:
            self.model.schedule = BaseScheduler(self)
            self.model.initialize_data_collector()
        self.assertEqual(
            str(cm.exception),
            "You must add agents to the scheduler before initializing the data collector.",
        )


if __name__ == "__main__":
    unittest.main()

"""
