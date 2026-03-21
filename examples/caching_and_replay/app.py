"""
Solara visualisation for the Schelling Caching and Replay example.

Run with:
    solara run app.py
"""

import mesa.visualization
from model import Schelling


def agent_portrayal(agent):
    return {
        "color": "#185FA5" if agent.type == 0 else "#D85A30",
        "marker": "s",
        "size": 25,
    }


model_params = {
    "height": 20,
    "width": 20,
    "homophily": {
        "type": "SliderInt",
        "value": 3,
        "label": "Homophily",
        "min": 0,
        "max": 8,
        "step": 1,
    },
    "density": {
        "type": "SliderFloat",
        "value": 0.8,
        "label": "Density",
        "min": 0.1,
        "max": 1.0,
        "step": 0.1,
    },
    "minority_pc": {
        "type": "SliderFloat",
        "value": 0.3,
        "label": "Minority fraction",
        "min": 0.0,
        "max": 1.0,
        "step": 0.05,
    },
    "radius": {
        "type": "SliderInt",
        "value": 1,
        "label": "Radius",
        "min": 1,
        "max": 5,
        "step": 1,
    },
    "rng": 42,
}

page = mesa.visualization.SolaraViz(
    Schelling,
    components=[
        mesa.visualization.make_space_component(agent_portrayal),
        mesa.visualization.make_plot_component(["happy"]),
    ],
    model_params=model_params,
    name="Schelling Segregation — with caching and replay",
)
page