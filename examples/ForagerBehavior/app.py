from mesa.visualization import SolaraViz, make_plot_component, make_space_component
from model import ForagerModel


def agent_portrayal(agent):
    if agent.state == "searching":
        return {"color": "#1D9E75", "size": 30}
    else:
        return {"color": "#4a4a8a", "size": 30}


model_params = {
    "n_agents": {
        "type": "SliderInt",
        "value": 10,
        "label": "Number of agents",
        "min": 1,
        "max": 30,
        "step": 1,
    },
    "resource_density": {
        "type": "SliderFloat",
        "value": 0.3,
        "label": "Resource density",
        "min": 0.1,
        "max": 0.8,
        "step": 0.1,
    },
    "width": {"type": "SliderInt", "value": 20, "min": 10, "max": 40, "step": 5},
    "height": {"type": "SliderInt", "value": 20, "min": 10, "max": 40, "step": 5},
}

page = SolaraViz(
    ForagerModel,
    components=[
        make_space_component(agent_portrayal),
        make_plot_component(["searching", "resting"]),
        make_plot_component(["total_resources"]),
    ],
    model_params=model_params,
    name="Forager Behavior Model",
)
page
