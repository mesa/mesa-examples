from matplotlib.markers import MarkerStyle

from mesa.visualization import Slider, SolaraViz, SpaceRenderer, make_plot_component
from mesa.visualization.components import AgentPortrayalStyle

from model import PredatorPreyModel
from agents import Prey, Predator


def agent_draw(agent):
    """Define how the agents look in the UI."""
    if isinstance(agent, Prey):
        return AgentPortrayalStyle(
            color="blue",
            size=15,
            marker="o"  # Circle for prey
        )
    elif isinstance(agent, Predator):
        return AgentPortrayalStyle(
            color="red",
            size=30,
            marker="^"  # Triangle for predator
        )


# Interactive sliders for the Solara UI
model_params = {
    "initial_prey": Slider(
        label="Initial Prey",
        value=100,
        min=10,
        max=300,
        step=10,
    ),
    "initial_predators": Slider(
        label="Initial Predators",
        value=20,
        min=1,
        max=100,
        step=5,
    ),
    "prey_reproduce": Slider(
        label="Prey Reproduction Rate",
        value=0.04,
        min=0.01,
        max=0.2,
        step=0.01,
    ),
    "predator_reproduce": Slider(
        label="Predator Reproduction Rate",
        value=0.05,
        min=0.01,
        max=0.2,
        step=0.01,
    ),
    "width": 100,
    "height": 100,
}


# Initialize the model
model = PredatorPreyModel()


# Set up the continuous space renderer
renderer = (
    SpaceRenderer(
        model,
        backend="matplotlib",
    )
    .setup_agents(agent_draw)
    .render()
)


# Set up the Population Line Chart
population_chart = make_plot_component(
    {"Prey": "blue", "Predators": "red"}
)


# Create the Solara webpage
page = SolaraViz(
    model,
    renderer,  # Pass renderer here as the second argument!
    components=[population_chart],  # ONLY the chart goes in the list!
    model_params=model_params,
    name="Continuous Space Predator-Prey",
)
page  # noqa
