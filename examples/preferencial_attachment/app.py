from mesa.visualization import (
    SolaraViz,
    make_plot_component,
    make_space_component,
)
from preferencial_attachment.model import AgentNetwork


def node_portrayal(agent):
    return {"color": "blue", "size": 30}


model_params = {
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "num": {
        "type": "SliderInt",
        "value": 30,
        "label": "No. of agents",
        "min": 10,
        "max": 100,
        "step": 1,
    },
}


def post_process_lineplot(ax):
    ax.set_ylim(ymin=0)
    ax.set_xlim(xmin=0)
    ax.set_ylabel("Nodes with Degree 1")
    ax.set_xlabel("Steps")


SpacePlot = make_space_component(node_portrayal)
StatePlot = make_plot_component(measure="Degree", post_process=post_process_lineplot)
model = AgentNetwork()

page = SolaraViz(
    model,
    components=[SpacePlot, StatePlot],
    model_params=model_params,
    name="Agent Network",
)
