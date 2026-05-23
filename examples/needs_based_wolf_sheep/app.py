from agents import NeedsBasedSheep, NeedsBasedWolf
from mesa.visualization import SolaraViz, make_plot_component
from model import NeedsBasedWolfSheep


def agent_portrayal(agent):
    if isinstance(agent, NeedsBasedWolf):
        return {"color": "tab:red", "size": 25}
    if isinstance(agent, NeedsBasedSheep):
        return {"color": "tab:cyan", "size": 15}
    return {}


model_params = {
    "initial_sheep": {
        "type": "SliderInt",
        "value": 200,
        "label": "Initial Sheep",
        "min": 10,
        "max": 400,
    },
    "initial_wolves": {
        "type": "SliderInt",
        "value": 15,
        "label": "Initial Wolves",
        "min": 5,
        "max": 100,
    },
    "sheep_reproduce": {
        "type": "SliderFloat",
        "value": 0.12,
        "label": "Sheep Reproduction Rate",
        "min": 0.01,
        "max": 0.2,
        "step": 0.01,
    },
    "wolf_reproduce": {
        "type": "SliderFloat",
        "value": 0.04,
        "label": "Wolf Reproduction Rate",
        "min": 0.01,
        "max": 0.1,
        "step": 0.01,
    },
}

PopulationPlot = make_plot_component({"Wolves": "tab:red", "Sheep": "tab:cyan"})

page = SolaraViz(
    NeedsBasedWolfSheep,
    components=[PopulationPlot],
    model_params=model_params,
    name="Needs-Based Wolf-Sheep",
)
