import solara
from mesa.visualization import (
    Slider,
    SolaraViz,
    make_plot_component,
    make_space_component,
)

from examples.schelling.model import Schelling


def get_happy_agents(model):
    """Display a text count of how many happy agents there are."""
    return solara.Markdown(
        "# Schelling model\n" f"**Happy agents: {model.happy}**",
        style={"width": "100%", "height": "200px"},
    )


def agent_portrayal(agent):
    return {"color": "tab:orange" if agent.type == 0 else "tab:blue"}


parameters = {
    "height": 20,
    "width": 20,
    "density": 0.8,
    "minority_pc": 0.5,
    "homophily": 0.4,
    "radius": 1,
}

model_params = {
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "density": Slider("Agent density", 0.8, 0.1, 1.0, 0.1),
    "minority_pc": Slider("Fraction minority", 0.2, 0.0, 1.0, 0.05),
    "homophily": Slider("Homophily", 0.4, 0.0, 1.0, 0.125),
    "width": {
        "type": "InputText",
        "value": 5,
        "label": "Width",
    },
    "height": {
        "type": "InputText",
        "value": 5,
        "label": "Height",
    },
}

model1 = Schelling(**parameters)

HappyPlot = make_plot_component({"happy": "tab:green"})

page = SolaraViz(
    model1,
    components=[
        make_space_component(agent_portrayal),
        HappyPlot,
        get_happy_agents,
    ],
    model_params=model_params,
)
page  # noqa
