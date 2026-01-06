"""
Visualization interface for the Rumor Mill model using Mesa's SolaraViz.
"""

from mesa.visualization import SolaraViz, SpaceRenderer, make_plot_component
from mesa.visualization.components import AgentPortrayalStyle
from rumor_mill.model import RumorMillModel


def agent_portrayal(agent):
    """
    Define how agents are displayed in the grid visualization.
    Red = knows rumor, Blue = doesn't know rumor
    """
    return AgentPortrayalStyle(color="red" if agent.knows_rumor else "blue", size=50)


# Model parameters that can be adjusted via UI sliders and checkboxes
model_params = {
    "know_rumor_ratio": {
        "type": "SliderFloat",
        "value": 0.3,
        "label": "Initial Percentage Knowing Rumor",
        "min": 0.0,
        "max": 1.0,
        "step": 0.01,
    },
    "rumor_spread_chance": {
        "type": "SliderFloat",
        "value": 0.5,
        "label": "Rumor Spread Chance",
        "min": 0.0,
        "max": 1.0,
        "step": 0.01,
    },
    "eight_neightborhood": {
        "type": "Checkbox",
        "value": False,
        "label": "Use Eight Neighborhood",
    },
    "width": 10,
    "height": 10,
}

# Create initial model instance
rumor_model = RumorMillModel(
    width=10,
    height=10,
    know_rumor_ratio=0.3,
    rumor_spread_chance=0.5,
    eight_neightborhood=False,
)

# Create grid renderer to visualize agents on the grid
renderer = SpaceRenderer(model=rumor_model, backend="matplotlib").render(
    agent_portrayal=agent_portrayal
)

# Create plot components to track metrics over time
rumor_spread_plot = make_plot_component(
    "Percentage_Knowing_Rumor",
    page=1,  # Track percentage who know rumor
)
times_heard_plot = make_plot_component(
    "Times_Heard_Rumor_Per_Step",
    page=1,  # Track total times rumor was heard this step
)
new_learners_percentage_plot = make_plot_component(
    "New_People_Knowing_Rumor",
    page=1,  # Track percentage of new learners per step
)

# Create the visualization page with all components
page = SolaraViz(
    rumor_model,
    renderer,
    components=[rumor_spread_plot, times_heard_plot, new_learners_percentage_plot],
    model_params=model_params,
    name="Rumor Mill Model",
)
