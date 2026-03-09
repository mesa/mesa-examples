from llm_epidemic.model import EpidemicModel
from mesa.visualization import SolaraViz, make_plot_component
from mesa.visualization.components.matplotlib_components import make_mpl_space_component


def agent_portrayal(agent):
    """Color agents based on their health state."""
    if not hasattr(agent, "health_state"):
        return {"color": "gray", "size": 30}

    color_map = {
        "susceptible": "#3498db",  # Blue
        "infected": "#e74c3c",  # Red
        "recovered": "#2ecc71",  # Green
    }
    color = color_map.get(agent.health_state, "gray")

    # Isolating agents shown with marker
    marker = "s" if agent.is_isolating else "o"

    return {"color": color, "size": 50, "marker": marker}


model_params = {
    "num_agents": {
        "type": "SliderInt",
        "value": 20,
        "label": "Number of Agents",
        "min": 5,
        "max": 50,
        "step": 1,
    },
    "initial_infected": {
        "type": "SliderInt",
        "value": 3,
        "label": "Initially Infected",
        "min": 1,
        "max": 10,
        "step": 1,
    },
    "grid_size": {
        "type": "SliderInt",
        "value": 10,
        "label": "Grid Size",
        "min": 5,
        "max": 20,
        "step": 1,
    },
    "llm_model": {
        "type": "Select",
        "value": "gemini/gemini-2.0-flash",
        "label": "LLM Model",
        "values": [
            "gemini/gemini-2.0-flash",
            "gpt-4o-mini",
            "gpt-4o",
        ],
    },
}

SpaceComponent = make_mpl_space_component(agent_portrayal)
SIRPlot = make_plot_component(
    {
        "susceptible_count": "#3498db",
        "infected_count": "#e74c3c",
        "recovered_count": "#2ecc71",
    }
)

page = SolaraViz(
    EpidemicModel,
    components=[SpaceComponent, SIRPlot],
    model_params=model_params,
    name="LLM Epidemic Model",
)
page
