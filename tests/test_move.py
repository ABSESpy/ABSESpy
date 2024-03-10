#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from typing import Tuple

import pytest

from abses.actor import Actor
from abses.cells import PatchCell
from abses.errors import ABSESpyError
from abses.main import MainModel


class TestMovements:
    """
    Test the movements of agents.
    """

    def test_move_to_cell(self, cell_0_0: PatchCell, cell_0_1: PatchCell):
        """Test the movement of agents."""
        # arrange
        actor = cell_0_1.agents.create(Actor, singleton=True)
        # action
        actor.move.to(cell_0_0)
        # assert
        assert actor.at is cell_0_0
        assert actor not in cell_0_1.agents
        assert cell_0_1.agents.is_empty

    def test_move_to_coordinate(
        self, model: MainModel, cell_0_1: PatchCell, cell_0_0: PatchCell
    ):
        """Test the movement of agents."""
        # arrange
        actor = model.agents.create(Actor, singleton=True)
        # action
        actor.move.to(cell_0_1.pos, cell_0_1.layer)
        # assert
        assert actor.at is cell_0_1
        actor.move.to((0, 0))
        assert actor.at is cell_0_0
        assert actor not in cell_0_1.agents

    def test_move_cross_layer(self, model: MainModel, cell_0_0: PatchCell):
        """Test raises error when move wrongly."""
        # arrange
        new_module = model.nature.create_module(
            how="from_resolution", shape=(1, 2)
        )
        actor = cell_0_0.agents.create(Actor, singleton=True)
        another_layer_cell = new_module.cells[0][0]
        # action
        with pytest.raises(ABSESpyError):
            actor.move.to(another_layer_cell)
        assert actor.at is cell_0_0
        cell_0_0.agents.remove(actor)
        actor.move.to(another_layer_cell)
        assert actor.at is another_layer_cell

    def test_move_off(self, cell_0_0: PatchCell):
        """Test the movement of agents."""
        # arrange
        actor = cell_0_0.agents.create(Actor, singleton=True)
        # action
        actor.move.off()
        # assert
        assert actor.at is None
        assert cell_0_0.agents.is_empty

    @pytest.mark.parametrize(
        "location, direction, distance, expected_loc",
        [
            ((0, 0), "up", 1, (1, 0)),
            ((0, 0), "down", 1, (1, 0)),
            ((0, 0), "left", 1, (0, 1)),
            ((0, 0), "right", 1, (0, 1)),
            ((0, 0), "left", 2, (0, 0)),
            ((0, 0), "up", 2, (0, 0)),
        ],
    )
    def test_move_by(
        self,
        cells,
        location: Tuple[int, int],
        direction: str,
        distance: int,
        expected_loc: tuple[int, int],
    ):
        """Test the movement of agents."""
        # arrange
        cell: PatchCell = cells[location[0], location[1]]
        actor = cell.agents.create(Actor, singleton=True)
        # action
        actor.move.by(direction=direction, distance=distance)
        # assert
        new_cell: PatchCell = cells[expected_loc[0], expected_loc[1]]
        assert (actor in cell.agents) is (new_cell is cell)
        assert actor in new_cell.agents
        assert actor.at is new_cell

    @pytest.mark.parametrize(
        "prob, include_center, expected",
        [
            ((1, 0, 1, 0), False, [(1, 0)]),
            ((1, 0, 0, 0), True, [(0, 0)]),
            ((1, 0, 0, 0), False, [(0, 1), (1, 0)]),
            ((0, 1, 0, 0), False, [(0, 1)]),
            ((1, 0, 0, 1), False, [(0, 1), (1, 0)]),
        ],
        ids=[
            "Not include center, must go to (1, 0).",
            "Include center, must stay at (0, 0).",
            "Not include center, average probability in (0, 1) or (1, 0)",
            "Not include center, must go to (0, 1)",
            "Not include center, not diag, average probability in (0, 1) or (1, 0)",
        ],
    )
    def test_random_move(
        self,
        cell_0_0: PatchCell,
        cell_0_1: PatchCell,
        cell_1_0: PatchCell,
        cell_1_1: PatchCell,
        prob: Tuple[int],
        expected: Tuple[int, int],
        include_center: bool,
    ):
        """测试随机移动"""
        # Arrange
        actor = cell_0_0.agents.create(Actor, singleton=True)
        cell_0_0.test = prob[0]
        cell_0_1.test = prob[1]
        cell_1_0.test = prob[2]
        cell_1_1.test = prob[3]
        # Act
        actor.move.random(prob="test", include_center=include_center)
        # Assert
        assert actor.at.pos in expected
