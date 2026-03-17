"""Schelling model visualization components.

Standard visualization for the Schelling segregation model.
"""

import solara
from mesa.visualization import make_plot_component, make_space_component
from mesa.visualization.components import AgentPortrayalStyle
from mesa.visualization.utils import update_counter
from model import Schelling


@solara.component
def get_happy_agents(model):
    """Display count and percentage of happy agents."""
    update_counter.get()

    total_agents = len(model.agents)
    happy_count = 0
    current_step = 0
    if hasattr(model, "datacollector") and model.datacollector.model_vars:
        try:
            data = model.datacollector.get_model_vars_dataframe()
            if not data.empty:
                current_step = len(data)
                if current_step > 0 and "happy" in data.columns:
                    happy_count = int(data["happy"].iloc[-1])
        except (IndexError, KeyError):
            pass

    if total_agents > 0:
        happy_percentage = (happy_count / total_agents) * 100

        solara.Markdown(
            f"**Happy agents:** {happy_count} / {total_agents} "
            f"({happy_percentage:.1f}%)"
        )
    else:
        solara.Markdown("**Happy agents:** 0 / 0")


def agent_portrayal(agent):
    """Define agent visualization properties."""
    if agent.type == 0:
        return AgentPortrayalStyle(color="red", size=50)
    return AgentPortrayalStyle(color="blue", size=50)


# Model parameters for the Schelling model
model_params = {
    "height": 20,
    "width": 20,
    "density": {
        "type": "SliderFloat",
        "value": 0.8,
        "label": "Agent density",
        "min": 0.1,
        "max": 1.0,
        "step": 0.1,
    },
    "minority_pc": {
        "type": "SliderFloat",
        "value": 0.2,
        "label": "Fraction minority",
        "min": 0.0,
        "max": 1.0,
        "step": 0.05,
    },
    "homophily": {
        "type": "SliderInt",
        "value": 3,
        "label": "Homophily",
        "min": 0,
        "max": 8,
        "step": 1,
    },
    "radius": {
        "type": "SliderInt",
        "value": 1,
        "label": "Search Radius",
        "min": 1,
        "max": 5,
        "step": 1,
    },
}

# Initialize model
model = Schelling()

# Create visualization components
space_component = make_space_component(agent_portrayal)
happy_chart = make_plot_component("happy")
