from mesa.visualization import SolaraViz, SpaceRenderer, make_plot_component
from mesa.visualization.components import AgentPortrayalStyle
from rumor_mill.model import RumorMillModel


def agent_portrayal(agent):
    if hasattr(agent, "agent_type") and agent.agent_type == "debunker":
        return AgentPortrayalStyle(color="green", size=80)
    return AgentPortrayalStyle(color="red" if agent.knows_rumor else "blue", size=50)


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
    "skepticism_mean": {
        "type": "SliderFloat",
        "value": 0.0,
        "label": "Mean Skepticism",
        "min": 0.0,
        "max": 1.0,
        "step": 0.01,
    },
    "forget_chance": {
        "type": "SliderFloat",
        "value": 0.0,
        "label": "Forget Chance",
        "min": 0.0,
        "max": 0.5,
        "step": 0.01,
    },
    "fraction_debunkers": {
        "type": "SliderFloat",
        "value": 0.0,
        "label": "Fraction Debunkers",
        "min": 0.0,
        "max": 0.5,
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

rumor_model = RumorMillModel()

renderer = SpaceRenderer(model=rumor_model, backend="matplotlib").render(
    agent_portrayal=agent_portrayal
)

rumor_spread_plot = make_plot_component("Percentage_Knowing_Rumor", page=1)
times_heard_plot = make_plot_component("Times_Heard_Rumor_Per_Step", page=1)
new_learners_plot = make_plot_component("New_People_Knowing_Rumor", page=1)
forgotten_plot = make_plot_component("Percentage_Forgotten", page=1)
debunker_plot = make_plot_component("Debunker_Effectiveness", page=1)

page = SolaraViz(
    rumor_model,
    renderer,
    components=[
        rumor_spread_plot,
        times_heard_plot,
        new_learners_plot,
        forgotten_plot,
        debunker_plot,
    ],
    model_params=model_params,
    name="Rumor Mill Model",
)

page  # noqa
