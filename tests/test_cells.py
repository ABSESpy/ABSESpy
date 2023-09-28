#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

import numpy as np
import pytest

from abses import ActorsList
from abses.main import MainModel
from abses.nature import PatchModule
from abses.tools.func import get_buffer


@pytest.fixture(name="cells")
def cells_list():
    """模拟一个斑块模块，包含5*5个格子"""
    model = MainModel()
    module = PatchModule.from_resolution(model, shape=(5, 5))
    return model, module.array_cells


def get_cells(array_cells, centre, radius, moor, annular, include_center):
    """获取合理的斑块"""
    zeros = np.zeros(shape=array_cells.shape)
    zeros[*centre] = 1
    arr = get_buffer(zeros, radius=radius, moor=moor, annular=annular)
    arr[*centre] = include_center
    return arr


@pytest.mark.parametrize(
    "centre, moore, radius, include_center, annular",
    [
        # Happy path tests
        ([2, 2], False, 1, False, False),  # Test case 1
        ([2, 2], True, 2, True, False),  # Test case 2
        ([2, 2], False, 3, True, True),  # Test case 3
        ([2, 2], True, 1, True, False),  # Test case 5
        ([2, 2], False, 2, True, True),  # Test case 6
        ([2, 2], True, 1, False, True),  # Test case 8
        ([2, 2], False, 2, False, True),  # Test case 9
    ],
    ids=[
        "Happy path - Test case 1",
        "Happy path - Test case 2",
        "Happy path - Test case 3",
        # "Edge case - Test case 4",
        "Edge case - Test case 5",
        "Edge case - Test case 6",
        # "Error case - Test case 7",
        "Error case - Test case 8",
        "Error case - Test case 9",
    ],
)
def test_get_neighboring_cells(
    cells, centre, moore, radius, include_center, annular
):
    """测试通过斑块搜索周围格子"""
    # Arrange
    model, array_cells = cells
    expected_mask = get_cells(
        array_cells, centre, radius, moore, annular, include_center
    )
    expected_cells = ActorsList(model, array_cells[expected_mask])
    # Act
    result = array_cells[*centre].get_neighboring_cells(
        moore, radius, include_center, annular
    )

    # Assert
    assert result == expected_cells
