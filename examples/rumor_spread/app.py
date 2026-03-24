from mesa.visualization import Slider, SolaraViz, SpaceRenderer, make_plot_component
from mesa.visualization.components.portrayal_components import AgentPortrayalStyle

from model import RumorModel


def portrayal(agent):
    """Visual style for rumor agents."""
    if agent is None:
        return None

    style = AgentPortrayalStyle(size=100, marker="s", zorder=1)
    if agent.has_rumor:
        style.update(("color", "red"))
    else:
        style.update(("color", "lightgray"))
    return style


def post_process_space(ax):
    """Improve readability of the grid plot."""
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])


model_params = {
    "initial_spreaders": Slider("Initial Spreaders", 2, 1, 20, 1),
    "infection_strength": Slider("Infection Strength", 0.2, 0.05, 0.5, 0.05),
    "recovery_rate": Slider("Recovery Rate", 0.05, 0.0, 0.3, 0.01),
}

model = RumorModel()

renderer = SpaceRenderer(model, backend="matplotlib").setup_agents(portrayal)
renderer.post_process = post_process_space
renderer.draw_agents()

plot_component = make_plot_component({"Informed": "tab:blue"})

page = SolaraViz(
    model,
    renderer,
    components=[plot_component],
    model_params=model_params,
    name="Rumor Spread Model",
)

page