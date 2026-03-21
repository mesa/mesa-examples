"""
Solara visualisation for the Shape Example.

Run with:
    solara run app.py
"""

import mesa.visualization
from model import ShapeExample


def agent_portrayal(agent):
    """Render each walker as an arrow pointing in its heading direction."""
    heading_to_angle = {
        (1, 0): 0,    # right
        (0, 1): 90,   # up
        (-1, 0): 180, # left
        (0, -1): 270, # down
    }
    return {
        "color": "#1D9E75",
        "shape": "arrowHead",
        "scale": 0.8,
        "heading_x": agent.heading[0],
        "heading_y": agent.heading[1],
    }


model_params = {
    "num_agents": {
        "type": "SliderInt",
        "value": 2,
        "label": "Number of agents",
        "min": 1,
        "max": 20,
        "step": 1,
    },
    "width": 20,
    "height": 10,
}

page = mesa.visualization.SolaraViz(
    ShapeExample,
    components=[
        mesa.visualization.make_space_component(agent_portrayal),
    ],
    model_params=model_params,
    name="Shape Example — directional agents on a grid",
)
page