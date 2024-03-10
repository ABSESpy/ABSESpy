#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""测试单元格。
1. 测试单元格能够选取它的邻居
2. 测试单元格的属性和方法
"""

from __future__ import annotations

import numpy as np
import pytest

from abses import ActorsList
from abses.actor import Actor
from abses.main import MainModel
from abses.nature import PatchModule
from abses.tools.func import get_buffer


class TestCellNeighboring:
    """测试单元格的邻居选取问题"""

    @pytest.fixture(name="array_cells")
    def cells_list(self, model: MainModel):
        """模拟一个斑块模块，包含5*5个格子"""
        module = PatchModule.from_resolution(model, shape=(5, 5))
        return module.array_cells

    @staticmethod
    def get_cells(array, centre, radius, moor, annular, include_center):
        """获取合理的数组"""
        zeros = np.zeros(shape=array.shape)
        zeros[centre[0], centre[1]] = 1
        mask = get_buffer(zeros, radius=radius, moor=moor, annular=annular)
        mask[centre[0], centre[1]] = include_center
        return mask

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
        self,
        model,
        array_cells,
        centre,
        moore,
        radius,
        include_center,
        annular,
    ):
        """测试通过斑块搜索周围格子"""
        # Arrange
        expected_mask = self.get_cells(
            array_cells, centre, radius, moore, annular, include_center
        )
        expected_cells = ActorsList(model, array_cells[expected_mask])
        # Act
        result = array_cells[centre[0], centre[1]].neighboring(
            moore, radius, include_center, annular
        )

        # Assert
        assert result == expected_cells


class TestPatchCell:
    """TestPatchCell"""

    def test_patch_cell_attachment(self, cell_0_0):
        """测试斑块可以连接到一个主体"""
        cell = cell_0_0
        actor = cell.agents.create(Actor, singleton=True)
        cell.link.to(actor, "actor_1")

        assert "actor_1" in cell.link
        assert cell.link == ("actor_1",)
        assert actor in cell.link.get("actor_1")
