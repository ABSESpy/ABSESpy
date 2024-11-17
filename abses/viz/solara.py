#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from typing import Any, Callable

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LinearSegmentedColormap, Normalize, to_rgba
from matplotlib.figure import Figure
from mesa.visualization.mpl_space_drawing import draw_orthogonal_grid
from mesa.visualization.utils import update_counter
from xarray import DataArray

from abses.main import MainModel
from abses.patch import PatchModule

try:
    import solara
except ImportError as e:
    raise ImportError(
        "`solara` is not installed, please install it via `pip install solara`"
    ) from e


def draw_property_layers(
    space: PatchModule,
    propertylayer_portrayal: dict[str, dict[str, Any]],
    ax: Axes,
):
    """Draw PropertyLayers on the given axes.

    Args:
        space (mesa.space._Grid): The space containing the PropertyLayers.
        propertylayer_portrayal (dict): the key is the name of the layer, the value is a dict with
                                        fields specifying how the layer is to be portrayed
        ax (matplotlib.axes.Axes): The axes to draw on.

    Notes:
        valid fields in in the inner dict of propertylayer_portrayal are "alpha", "vmin", "vmax", "color" or "colormap", and "colorbar"
        so you can do `{"some_layer":{"colormap":'viridis', 'alpha':.25, "colorbar":False}}`

    """
    for layer_name, portrayal in propertylayer_portrayal.items():
        layer: DataArray = space.get_xarray(layer_name)

        data = (
            layer.data.astype(float)
            if layer.data.dtype == bool
            else layer.data
        )

        # Get portrayal properties, or use defaults
        alpha = portrayal.get("alpha", 1)
        vmin = portrayal.get("vmin", np.min(data))
        vmax = portrayal.get("vmax", np.max(data))
        colorbar = portrayal.get("colorbar", True)

        # Draw the layer
        if "color" in portrayal:
            rgba_color = to_rgba(portrayal["color"])
            normalized_data = (data - vmin) / (vmax - vmin)
            rgba_data = np.full((*data.shape, 4), rgba_color)
            rgba_data[..., 3] *= normalized_data * alpha
            rgba_data = np.clip(rgba_data, 0, 1)
            cmap = LinearSegmentedColormap.from_list(
                layer_name, [(0, 0, 0, 0), (*rgba_color[:3], alpha)]
            )
            im = ax.imshow(
                rgba_data.transpose(1, 0, 2),
                origin="lower",
            )
            if colorbar:
                norm = Normalize(vmin=vmin, vmax=vmax)
                sm = ScalarMappable(norm=norm, cmap=cmap)
                sm.set_array([])
                ax.figure.colorbar(sm, ax=ax, orientation="vertical")

        elif "colormap" in portrayal:
            cmap = portrayal.get("colormap", "viridis")
            if isinstance(cmap, list):
                cmap = LinearSegmentedColormap.from_list(layer_name, cmap)
            im = ax.imshow(
                data.T,
                cmap=cmap,
                alpha=alpha,
                vmin=vmin,
                vmax=vmax,
                origin="lower",
            )
            if colorbar:
                plt.colorbar(im, ax=ax, label=layer_name)
        else:
            raise ValueError(
                f"PropertyLayer {layer_name} portrayal must include 'color' or 'colormap'."
            )


@solara.component
def SpaceMatplotlib(
    model: MainModel,
    agent_portrayal,
    propertylayer_portrayal,
    dependencies: list[Any] | None = None,
    post_process: Callable | None = None,
    **space_drawing_kwargs,
):
    """Create a Matplotlib-based space visualization component."""
    update_counter.get()
    if model.nature.major_layer is None:
        raise ValueError("Major layer is not set for the nature.")
    space = model.nature.major_layer

    fig = Figure()
    ax = fig.add_subplot()

    draw_orthogonal_grid(
        space,
        agent_portrayal,
        ax=ax,
        **space_drawing_kwargs,
    )

    if post_process is not None:
        post_process(ax)

    solara.FigureMatplotlib(
        fig, format="png", bbox_inches="tight", dependencies=dependencies
    )

    if propertylayer_portrayal:
        draw_property_layers(space, propertylayer_portrayal, ax=ax)


def make_mpl_space_component(
    agent_portrayal: Callable | None = None,
    propertylayer_portrayal: dict | None = None,
    post_process: Callable | None = None,
    **space_drawing_kwargs,
) -> Callable:
    """Create a Matplotlib-based space visualization component.

    Args:
        agent_portrayal: Function to portray agents.
        propertylayer_portrayal: Dictionary of PropertyLayer portrayal specifications
        post_process : a callable that will be called with the Axes instance. Allows for fine tuning plots (e.g., control ticks)
        space_drawing_kwargs : additional keyword arguments to be passed on to the underlying space drawer function. See
                               the functions for drawing the various spaces for further details.

    ``agent_portrayal`` is called with an agent and should return a dict. Valid fields in this dict are "color",
    "size", "marker", "zorder", alpha, linewidths, and edgecolors. Other field are ignored and will result in a user warning.

    Returns:
        function: A function that creates a SpaceMatplotlib component
    """
    if agent_portrayal is None:

        def agent_portrayal(a):
            return {}

    def MakeSpaceMatplotlib(model):
        return SpaceMatplotlib(
            model,
            agent_portrayal,
            propertylayer_portrayal,
            post_process=post_process,
            **space_drawing_kwargs,
        )

    return MakeSpaceMatplotlib
