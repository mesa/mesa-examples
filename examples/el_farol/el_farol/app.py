"""
Solara visualisation for the El Farol Bar model.

Run with:
    solara run app.py
"""

import mesa.visualization
from model import ElFarolBar

model_params = {
    "num_agents": {
        "type": "SliderInt",
        "value": 100,
        "label": "Number of agents",
        "min": 10,
        "max": 300,
        "step": 10,
    },
    "crowd_threshold": {
        "type": "SliderInt",
        "value": 60,
        "label": "Crowd threshold",
        "min": 1,
        "max": 100,
        "step": 1,
    },
    "num_strategies": {
        "type": "SliderInt",
        "value": 10,
        "label": "Strategies per agent",
        "min": 1,
        "max": 20,
        "step": 1,
    },
    "memory_size": {
        "type": "SliderInt",
        "value": 10,
        "label": "Memory size",
        "min": 1,
        "max": 20,
        "step": 1,
    },
}

page = mesa.visualization.SolaraViz(
    ElFarolBar,
    components=[
        mesa.visualization.make_plot_component(["Customers"]),
    ],
    model_params=model_params,
    name="El Farol Bar Model",
)
page
