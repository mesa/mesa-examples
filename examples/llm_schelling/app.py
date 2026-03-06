import matplotlib.pyplot as plt
import numpy as np
import solara
from llm_schelling.model import LLMSchellingModel
from mesa.visualization import SolaraViz, make_plot_component
from mesa.visualization.utils import update_counter

GROUP_COLORS = {0: "#2196F3", 1: "#FF5722"}  # Blue, Orange

model_params = {
    "width": {
        "type": "SliderInt",
        "value": 10,
        "label": "Grid width",
        "min": 5,
        "max": 20,
        "step": 1,
    },
    "height": {
        "type": "SliderInt",
        "value": 10,
        "label": "Grid height",
        "min": 5,
        "max": 20,
        "step": 1,
    },
    "density": {
        "type": "SliderFloat",
        "value": 0.8,
        "label": "Population density",
        "min": 0.1,
        "max": 1.0,
        "step": 0.05,
    },
    "minority_fraction": {
        "type": "SliderFloat",
        "value": 0.4,
        "label": "Minority fraction",
        "min": 0.1,
        "max": 0.5,
        "step": 0.05,
    },
}


def SchellingGridPlot(model):
    """Visualize the grid showing agent groups and happiness."""
    update_counter.get()

    width = model.grid.dimensions[0]
    height = model.grid.dimensions[1]

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Schelling Segregation (LLM)\nBlue=Group A, Orange=Group B, X=Unhappy")

    for agent in model.agents:
        x, y = agent.pos
        color = GROUP_COLORS[agent.group]
        marker = "o" if agent.is_happy else "x"
        ax.plot(x + 0.5, y + 0.5, marker=marker, color=color,
                markersize=8, markeredgewidth=2)

    return solara.FigureMatplotlib(fig)


HappinessPlot = make_plot_component({"happy": "#4CAF50", "unhappy": "#F44336"})
SegregationPlot = make_plot_component("segregation_index")

model = LLMSchellingModel()

page = SolaraViz(
    model,
    components=[
        SchellingGridPlot,
        HappinessPlot,
        SegregationPlot,
    ],
    model_params=model_params,
    name="LLM Schelling Segregation",
)
