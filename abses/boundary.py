#!/usr/bin/env python
# -*-coding:utf-8 -*-
# Created date: 2022/1/14
# @Author  : Shuang Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import logging

import numpy as np

# from .tools.plot_heatmap import custom_cmap_heatmap, matrix_heatmap

logger = logging.getLogger(__name__)


class Boundaries:
    BOUNDARIES = ["outside", "interior", "boundaries", "special_boundaries"]

    def __init__(self, shape):
        self.shape = shape
        self._special_boundaries = {}  # Named boundaries' dict.
        self._boundaries = np.zeros(shape, dtype=bool)
        self._outside = np.zeros(shape, dtype=bool)
        self._interior = np.ones(shape, dtype=bool)
        self._update_all()

    @property
    def boundaries(self):
        """All boundaries."""
        return self._boundaries

    @property
    def special_boundaries(self):
        """Named special boundaries."""
        return self._special_boundaries

    @property
    def outside(self):
        """Outside the boundary."""
        return self._outside

    @property
    def interior(self):
        return self._interior

    def _check_shape(self, ndarray):
        """Check if the input ndarray's shape can fit in."""
        if ndarray.shape != self.shape:
            raise ValueError("shape must be 2d")
        else:
            return True

    def _update_all(self):
        """Update all boundaries"""
        changed_boundaries = self._update_boundaries()
        changed_interior = self._update_interior()
        changed = changed_boundaries == changed_interior
        perfect_change = changed.all()
        if not perfect_change:
            logger.warning("Update not perfect!")
        return changed

    def _update_interior(self):
        """Update interior mask by the boundaries mask."""
        new_interior = ~(self.boundaries | self.outside)
        changed = self.interior != new_interior
        self.reset_boundary("interior", new_interior)
        return changed

    def _update_boundaries(self):
        """Update all boundary according to all types of boundary."""
        new_boundary = self.boundaries
        for bc_type in self.special_boundaries:
            new_boundary = new_boundary | self.special_boundaries[bc_type]
        changed = self.boundaries != new_boundary
        self.reset_boundary("boundaries", new_boundary)
        return changed

    def init_simple_boundaries(self, shape: tuple, settings: dict = None):
        outsides = settings.pop("outsides", 0)
        border = settings.pop("border", 1)
        return generate_simple_boundaries(
            shape=shape,
            boundary=self,
            outsides=outsides,
            border=border,
        )

    def change_special_boundary(self, name, patch):
        """Update a special boundary."""
        self._check_shape(patch)
        self._special_boundaries[name] = patch
        self._update_all()

    def reset_boundary(self, boundary_type: str, ndarray: np.ndarray):
        """Update any type of boundary (default or named)."""
        self._check_shape(ndarray)
        if hasattr(self, boundary_type):
            setattr(self, f"_{boundary_type}", ndarray)
        elif boundary_type in self.special_boundaries:
            self.change_special_boundary(boundary_type, ndarray)
        else:
            raise KeyError(f"No boundary type named {boundary_type}.")
        return ndarray

    # def plot_boundaries(self, bc_type="all", annotate_names=False, **kwargs):
    #     default_bc_type = ("boundaries", "interior", "outside")
    #     colors_map = {
    #         "Interior": "gray",
    #         "Boundary": "black",
    #         "Outside": "lightgray",
    #     }
    #     if annotate_names:
    #         annot = np.ones(self.shape, dtype=str)
    #         annot.fill("")
    #         for name, named_matrix in self.special_boundaries.items():
    #             annot[named_matrix] = name.capitalize()[0]
    #         kwargs["annot"] = annot
    #         kwargs["fmt"] = ""

    #     if bc_type == "all":
    #         outside = self.outside
    #         boundaries = self.boundaries
    #         interior = self.interior
    #         matrix = 0 * interior + 0.5 * boundaries + outside
    #         ax = custom_cmap_heatmap(
    #             matrix, colors_map, vmin=0, vmax=1, **kwargs
    #         )

    #     elif bc_type in default_bc_type:
    #         matrix = self.__getattribute__(bc_type)
    #         ax = matrix_heatmap(
    #             matrix, how="mask", title=f"{bc_type}", **kwargs
    #         )

    #     else:
    #         raise KeyError(f"{bc_type} not in {default_bc_type}.")
    #     return ax


def set_value_to_border(ndarray, thickness, value):
    """
    Set a 2d array's border to a specified value.

    Arguments:
        ndarray -- The ndarray to change.
        thickness -- Thickness of the border to change value.
        value -- Change into this value.

    Returns:
        An updated numpy 2D array object.
    """
    ndarray[0:thickness, :] = value
    ndarray[-thickness:, :] = value
    ndarray[:, 0:thickness] = value
    ndarray[:, -thickness:] = value
    return ndarray


def border_mask(shape, thickness):
    mask = np.zeros(shape, bool)
    set_value_to_border(mask, thickness, True)
    return mask


def generate_simple_boundaries(
    shape: tuple,
    outsides: int = 0,
    border: int = 1,
    boundary: Boundaries = None,
    **kwargs,
) -> Boundaries:
    """
    Generate the simplest boundary object.

    Arguments:
        shape -- Shape of the world, a 2D tuple.

    Keyword Arguments:
        outsides -- thickness of the outside area (default: {0}).
        border_thickness -- thickness of the border (default: {1}).
        boundary -- Boundaries object to update, or create a new one (default {None}).

    Returns:
        World's boundary object.
    """
    # 默认的边界是不同的
    if not boundary:
        boundary = Boundaries(shape=shape, **kwargs)
    if outsides > 0:
        outsides_ndarray = np.zeros(shape, dtype=bool)
        outsides_ndarray = set_value_to_border(
            outsides_ndarray, outsides, True
        )
        boundary.reset_boundary("outside", outsides_ndarray)
    if border > 0:
        border_ndarray = np.zeros(shape, dtype=bool)
        border_ndarray = set_value_to_border(
            border_ndarray, border + outsides, True
        )
        border_ndarray = set_value_to_border(border_ndarray, outsides, False)
        boundary.reset_boundary("boundaries", border_ndarray)
    boundary._update_interior()

    # Named special boundaries.
    left = np.zeros(shape, dtype=bool)
    left[
        outsides + border : -outsides - border, outsides : outsides + border
    ] = True
    right = np.zeros(shape, dtype=bool)
    right[
        outsides + border : -outsides - border,
        -outsides - border : shape[1] - outsides,
    ] = True
    # TODO Patches
    top = np.zeros(shape, dtype=bool)
    top[outsides : outsides + border, outsides : shape[1] - outsides] = True
    bottom = np.zeros(shape, dtype=bool)
    bottom[
        -outsides - border : shape[0] - outsides,
        outsides : shape[1] - outsides,
    ] = True

    boundary.change_special_boundary(name="left", patch=left)
    boundary.change_special_boundary(name="right", patch=right)
    boundary.change_special_boundary(name="top", patch=top)
    boundary.change_special_boundary(name="bottom", patch=bottom)
    boundary._update_all()
    return boundary


def simple_boundary_from(settings: dict):
    def parsing_shape(settings) -> tuple:
        y = settings.get("width", 8)
        x = settings.get("height", 6)
        shape = (x, y)
        return shape

    outside = settings.pop("outside", 0)
    border = settings.pop("border", 1)
    shape = parsing_shape(settings)
    boundary = generate_simple_boundaries(shape, outside, border)
    return boundary
