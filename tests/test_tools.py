#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import pytest

from abses import MainModel
from abses.objects import _BaseObj
from abses.time import time_condition
from abses.tools.func import iter_func


def test_iter_function():
    class Test:
        def __init__(self):
            self.elements = []

        @iter_func("elements")
        def testing(self, word: str):
            self.foo = word

    class Element(object):
        def testing(self, word):
            self.foo = word
            self.check = f"{self.foo} added auto."

    main = Test()
    comp1 = Element()
    comp2 = Element()

    main.elements.extend([comp1, comp2])
    main.testing("hello")
    assert main.foo == comp1.foo == comp2.foo == "hello"
    assert comp2.check == comp1.check == "hello added auto."


@pytest.fixture(name="mock_object")
def fixture_mock_object():
    model = MainModel(parameters={"time": {"start": "2000", "months": 1}})

    class MockObject(_BaseObj):
        def __init__(self, model):
            super().__init__(model)

        @time_condition(condition={"year": 2000, "month": 1})
        def my_method(self):
            return "This method runs only if the `time` attribute is in September 2023."

    return MockObject(model=model)


# Happy path tests
def test_time_condition_happy_path(mock_object):
    # Arrange

    # Act
    result = mock_object.my_method()

    # Assert
    assert (
        result
        == "This method runs only if the `time` attribute is in September 2023."
    )
    mock_object.model.time.go()
    assert not mock_object.my_method()


# Error cases
def test_time_condition_error_cases():
    class MockObj:
        def __init__(self) -> None:
            self.time = None

        def my_method():
            return "should not be called"

    # Arrange
    mock_object = MockObj()

    # Act and Assert
    with pytest.raises(TypeError):
        mock_object.my_method()
