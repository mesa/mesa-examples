"""
Solara visualization for the Needs-Based Wolf-Sheep model.

Run with: solara run app.py
"""

from agents import NeedsGrass, NeedsSheep, NeedsWolf
from mesa.experimental.devs import ABMSimulator
from mesa.visualization import SolaraViz, make_plot_component, make_space_component
from model import NeedsWolfSheep


def agent_portrayal(agent):
    """Define how agents are drawn on the grid."""
    if isinstance(agent, NeedsWolf):
        # Wolf color darkens with hunger (more red = more hungry)
        hunger_intensity = int(200 + 55 * agent.hunger)
        return {
            "color": f"#{hunger_intensity:02x}3232",
            "marker": "s",  # Square
            "size": 40,
        }
    elif isinstance(agent, NeedsSheep):
        # Sheep color changes with fear (more blue = more afraid)
        fear_intensity = int(100 + 155 * agent.fear)
        return {
            "color": f"#6464{fear_intensity:02x}",
            "marker": "o",  # Circle
            "size": 30,
        }
    elif isinstance(agent, NeedsGrass):
        if agent.fully_grown:
            return {"color": "#00aa00", "marker": "s", "size": 75}
        else:
            return {"color": "#c8b478", "marker": "s", "size": 75}
    return {}


model_params = {
    "width": {
        "type": "SliderInt",
        "value": 20,
        "label": "Grid Width",
        "min": 10,
        "max": 40,
        "step": 1,
    },
    "height": {
        "type": "SliderInt",
        "value": 20,
        "label": "Grid Height",
        "min": 10,
        "max": 40,
        "step": 1,
    },
    "initial_sheep": {
        "type": "SliderInt",
        "value": 100,
        "label": "Initial Sheep",
        "min": 10,
        "max": 300,
        "step": 10,
    },
    "initial_wolves": {
        "type": "SliderInt",
        "value": 25,
        "label": "Initial Wolves",
        "min": 5,
        "max": 100,
        "step": 5,
    },
    "sheep_reproduce": {
        "type": "SliderFloat",
        "value": 0.04,
        "label": "Sheep Reproduction Rate",
        "min": 0.01,
        "max": 0.1,
        "step": 0.01,
    },
    "wolf_reproduce": {
        "type": "SliderFloat",
        "value": 0.05,
        "label": "Wolf Reproduction Rate",
        "min": 0.01,
        "max": 0.1,
        "step": 0.01,
    },
    "grass_regrowth_time": {
        "type": "SliderInt",
        "value": 30,
        "label": "Grass Regrowth Time",
        "min": 5,
        "max": 60,
        "step": 5,
    },
}

# Population dynamics plot
PopulationPlot = make_plot_component(
    {"Wolves": "red", "Sheep": "blue", "Grass": "green"}
)

# Needs metrics plot
NeedsPlot = make_plot_component(
    {"Avg Wolf Hunger": "darkred", "Avg Sheep Fear": "darkblue"}
)

simulator = ABMSimulator()
model = NeedsWolfSheep(simulator=simulator)

page = SolaraViz(
    model,
    components=[
        make_space_component(agent_portrayal),
        PopulationPlot,
        NeedsPlot,
    ],
    model_params=model_params,
    name="Needs-Based Wolf-Sheep Predation",
    simulator=simulator,
)
