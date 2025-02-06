#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import contextlib
import warnings
from typing import Any, Callable

import matplotlib.pyplot as plt
import numpy as np
import solara
from matplotlib.axes import Axes
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LinearSegmentedColormap, Normalize, to_rgba
from matplotlib.figure import Figure
from mesa.visualization.mpl_space_drawing import _scatter
from mesa.visualization.utils import update_counter
from xarray import DataArray

from abses.main import MainModel
from abses.patch import PatchModule


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

        data = layer.data.astype(float) if layer.data.dtype == bool else layer.data

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


def collect_agent_data(
    space: PatchModule,
    agent_portrayal: Callable,
    color="tab:blue",
    size=25,
    marker="o",
    zorder: int = 1,
):
    """Collect the plotting data for all agents in the space.

    Args:
        space: The space containing the Agents.
        agent_portrayal: A callable that is called with the agent and returns a dict
        color: default color
        size: default size
        marker: default marker
        zorder: default zorder

    agent_portrayal should return a dict, limited to size (size of marker), color (color of marker), zorder (z-order),
    marker (marker style), alpha, linewidths, and edgecolors

    """
    arguments: dict[str, list[Any]] = {
        "s": [],
        "c": [],
        "marker": [],
        "zorder": [],
        "alpha": [],
        "edgecolors": [],
        "linewidths": [],
    }

    for agent in space.agents:
        portray = agent_portrayal(agent)
        arguments["s"].append(portray.pop("size", size))
        arguments["c"].append(portray.pop("color", color))
        arguments["marker"].append(portray.pop("marker", marker))
        arguments["zorder"].append(portray.pop("zorder", zorder))

        for entry in ["alpha", "edgecolors", "linewidths"]:
            with contextlib.suppress(KeyError):
                arguments[entry].append(portray.pop(entry))

        if len(portray) > 0:
            ignored_fields = list(portray.keys())
            msg = ", ".join(ignored_fields)
            warnings.warn(
                f"the following fields are not used in agent portrayal and thus ignored: {msg}.",
                stacklevel=2,
            )
    # ensure loc is always a shape of (n, 2) array, even if n=0
    result = {k: np.asarray(v) for k, v in arguments.items()}
    result["loc"] = space.agents.array("indices")
    return result


def draw_orthogonal_grid(
    space: PatchModule,
    agent_portrayal: Callable,
    ax: Axes | None = None,
    draw_grid: bool = True,
    **kwargs,
):
    """Visualize a orthogonal grid.

    Args:
        space: the space to visualize
        agent_portrayal: a callable that is called with the agent and returns a dict
        ax: a Matplotlib Axes instance. If none is provided a new figure and ax will be created using plt.subplots
        draw_grid: whether to draw the grid
        kwargs: additional keyword arguments passed to ax.scatter

    Returns:
        Returns the Axes object with the plot drawn onto it.

    ``agent_portrayal`` is called with an agent and should return a dict. Valid fields in this dict are "color",
    "size", "marker", and "zorder". Other field are ignored and will result in a user warning.

    """
    if ax is None:
        fig, ax = plt.subplots()

    # gather agent data
    s_default = (180 / max(space.width, space.height)) ** 2
    arguments = collect_agent_data(space, agent_portrayal, size=s_default)

    # plot the agents
    _scatter(ax, arguments, **kwargs)

    # further styling
    ax.set_xlim(-0.5, space.width - 0.5)
    ax.set_ylim(-0.5, space.height - 0.5)

    if draw_grid:
        # Draw grid lines
        for x in np.arange(-0.5, space.width - 0.5, 1):
            ax.axvline(x, color="gray", linestyle=":")
        for y in np.arange(-0.5, space.height - 0.5, 1):
            ax.axhline(y, color="gray", linestyle=":")

    return ax


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
