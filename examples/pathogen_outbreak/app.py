from mesa.visualization import SolaraViz, make_space_component, make_plot_component
from model import dis_Model


def make_agent(agent):
    color_map = {
        "healthy": "tab:green",
        "infected": "tab:orange",
        "immune": "tab:blue",
        "dead": "tab:red",
    }
    return {
        "color": color_map.get(agent.state, "black"),
        "size": 20,
        "marker": "s" if not agent.compliant else "o",
    }


model_params = {
    "compliance": {
        "type": "SliderFloat",
        "value": 0.7,
        "label": "Quarantine Compliance Rate",
        "min": 0.0,
        "max": 1.0,
        "step": 0.1,
    },
    "n": {
        "type": "SliderInt",
        "value": 100,
        "label": "Citizens",
        "min": 10,
        "max": 300,
        "step": 10,
    },
    "infn": {
        "type": "SliderInt",
        "value": 5,
        "label": "Infected",
        "min": 1,
        "max": 20,
        "step": 1,
    },
    "width": {"type": "SliderInt", "value": 20, "label": "Width", "min": 10, "max": 50},
    "height": {
        "type": "SliderInt",
        "value": 20,
        "label": "Height",
        "min": 10,
        "max": 50,
    },
}

model = dis_Model(n=100, infn=5, width=25, height=25)

renderer = make_space_component(make_agent)

graph_ot = make_plot_component(["healthy", "infected", "immune", "dead", "quarantine"])

page = SolaraViz(
    model,
    components=[renderer, graph_ot],
    model_params=model_params,
    name="Compliance/Quarantine during Outbreak Model",
)
