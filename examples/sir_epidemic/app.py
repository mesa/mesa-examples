"""SIR Epidemic Model - Visualization.

Run with: solara run app.py
"""

from mesa.visualization import SolaraViz, make_plot_component, make_space_component
from model import Person, SIRModel

# Color mapping for agent states
STATE_COLORS = {
    "Susceptible": "tab:blue",
    "Infected": "tab:red",
    "Recovered": "tab:green",
}


def agent_portrayal(agent):
    """Define how agents are displayed on the grid."""
    if not isinstance(agent, Person):
        return None
    return {
        "color": STATE_COLORS.get(agent.state, "tab:gray"),
        "marker": "o",
        "size": 30,
    }


model_params = {
    "num_agents": {
        "type": "SliderInt",
        "value": 100,
        "label": "Number of Agents",
        "min": 10,
        "max": 300,
        "step": 10,
    },
    "width": 20,
    "height": 20,
    "infection_rate": {
        "type": "SliderFloat",
        "value": 0.3,
        "label": "Infection Rate",
        "min": 0.0,
        "max": 1.0,
        "step": 0.05,
    },
    "recovery_time": {
        "type": "SliderInt",
        "value": 10,
        "label": "Recovery Time (steps)",
        "min": 1,
        "max": 30,
        "step": 1,
    },
    "initial_infected": {
        "type": "SliderInt",
        "value": 3,
        "label": "Initial Infected",
        "min": 1,
        "max": 20,
        "step": 1,
    },
    "seed": 42,
}

# Create visualization
page = SolaraViz(
    SIRModel,
    components=[
        make_space_component(agent_portrayal),
        make_plot_component(["Susceptible", "Infected", "Recovered"]),
    ],
    model_params=model_params,
    name="SIR Epidemic Model",
)

page  # noqa: B018
