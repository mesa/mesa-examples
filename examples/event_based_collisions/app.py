import matplotlib
from event_based_collisions.model import DiscModel
from mesa.visualization import (
    Slider,
    SolaraViz,
    make_space_component,
)
from mesa.visualization.components import AgentPortrayalStyle

# Setup model parameters for the visualization interface
model = DiscModel()
simulator = model.devs


model_params = {
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "n_discs": Slider(
        label="Number of discs",
        value=4,
        min=1,
        max=10,
        step=1,
    ),
    "disc_speed": Slider(
        label="Disc speed",
        value=1,
        min=1,
        max=10,
        step=1,
    ),
}

# Give each disc a different color
colormap = matplotlib.pyplot.get_cmap("tab10")


def agent_portrayal(agent):
    """Portray an agent for visualization."""
    return AgentPortrayalStyle(color=colormap(agent.id / 9))


agent_portrayal_component = make_space_component(
    agent_portrayal=agent_portrayal,
    backend="matplotlib",
)

page = SolaraViz(
    model,
    components=[
        agent_portrayal_component,
    ],
    model_params=model_params,
    name="Event Based Collisions",
)

page  # noqa
