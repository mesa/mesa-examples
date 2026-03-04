from mesa.visualization import SolaraViz, make_plot_component, make_space_component

from .model import SEIRModel

# Color mapping for each state
STATE_COLORS = {
    "S": "#3498db",  # Blue
    "E": "#f39c12",  # Orange
    "I": "#e74c3c",  # Red
    "R": "#2ecc71",  # Green
}


def agent_portrayal(agent):
    return {
        "color": STATE_COLORS.get(agent.state, "grey"),
        "size": 20,
    }


model_params = {
    "width": {
        "type": "SliderInt",
        "value": 30,
        "min": 10,
        "max": 50,
        "step": 5,
        "label": "Grid Width",
    },
    "height": {
        "type": "SliderInt",
        "value": 30,
        "min": 10,
        "max": 50,
        "step": 5,
        "label": "Grid Height",
    },
    "initial_infected": {
        "type": "SliderInt",
        "value": 5,
        "min": 1,
        "max": 20,
        "step": 1,
        "label": "Initial Infected",
    },
    "transmission_rate": {
        "type": "SliderFloat",
        "value": 0.3,
        "min": 0.0,
        "max": 1.0,
        "step": 0.05,
        "label": "Transmission Rate",
    },
    "incubation_period": {
        "type": "SliderInt",
        "value": 3,
        "min": 1,
        "max": 10,
        "step": 1,
        "label": "Incubation Period (days)",
    },
    "infection_duration": {
        "type": "SliderInt",
        "value": 7,
        "min": 1,
        "max": 21,
        "step": 1,
        "label": "Infection Duration (days)",
    },
    "vaccination_threshold": {
        "type": "SliderFloat",
        "value": 0.1,
        "min": 0.0,
        "max": 0.5,
        "step": 0.01,
        "label": "Vaccination Threshold",
    },
    "vaccination_rate": {
        "type": "SliderFloat",
        "value": 0.05,
        "min": 0.0,
        "max": 0.3,
        "step": 0.01,
        "label": "Vaccination Rate per Campaign",
    },
}

model = SEIRModel()

space_component = make_space_component(agent_portrayal)
epidemic_plot = make_plot_component(["Susceptible", "Exposed", "Infected", "Recovered"])
vaccination_plot = make_plot_component(["Vaccination Active"])

page = SolaraViz(
    model,
    components=[space_component, epidemic_plot, vaccination_plot],
    model_params=model_params,
    name="SEIR Epidemic Model with Vaccination Policy",
)
