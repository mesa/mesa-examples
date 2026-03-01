from boltzmann_wealth_model_network.model import BoltzmannWealthModelNetwork
from mesa.mesa_logging import INFO, log_to_stderr
from mesa.visualization import (
    SolaraViz,
    make_plot_component,
    make_space_component,
)

log_to_stderr(INFO)


# Tells Solara how to draw each agent.
def agent_portrayal(agent):
    return {
        "color": agent.wealth,  # using a colormap to convert wealth to color
        "size": 50,
    }


model_params = {
    "rng": {
        "type": "InputText",
        "value": 42,
        "label": "Random seed",
    },
    "n": {
        "type": "SliderInt",
        "value": 7,
        "label": "Number of agents",
        "min": 2,
        "max": 10,
        "step": 1,
        # "description": "Choose how many agents to include in the model",
    },
    "num_nodes": {
        "type": "SliderInt",
        "value": 10,
        "label": "Number of nodes",
        "min": 3,
        "max": 12,
        "step": 1,
        # "description": "Choose how many nodes to include in the model, with at least the same number of agents",
    },
}


def post_process(ax):
    ax.get_figure().colorbar(ax.collections[0], label="wealth", ax=ax)


# Create initial model instance
money_model = BoltzmannWealthModelNetwork(n=7, num_nodes=10, rng=42)

# Create visualization elements. The visualization elements are Solara
# components that receive the model instance as a "prop" and display it in a
# certain way. Under the hood these are just classes that receive the model
# instance. You can also author your own visualization elements, which can also
# be functions that receive the model instance and return a valid Solara
# component.

SpaceGraph = make_space_component(
    agent_portrayal, cmap="viridis", vmin=0, vmax=10, post_process=post_process
)
GiniPlot = make_plot_component("Gini")

# Create the SolaraViz page. This will automatically create a server and display
# the visualization elements in a web browser.
#
# Display it using the following command in the example directory:
#   solara run app.py
# It will automatically update and display any changes made to this file.

page = SolaraViz(
    money_model,
    components=[SpaceGraph, GiniPlot],
    model_params=model_params,
    name="Boltzmann Wealth Model: Network",
)
page  # noqa


# In a notebook environment, we can also display the visualization elements
# directly.
#
#   SpaceGraph(model1)
#   GiniPlot(model1)

# The plots will be static. If you want to pick up model steps,
# you have to make the model reactive first
#
#   reactive_model = solara.reactive(model1)
#   SpaceGraph(reactive_model)

# In a different notebook block:
#
#   reactive_model.value.step()
