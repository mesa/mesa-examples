from mesa.visualization import SolaraViz, make_plot_component
from mesa.visualization.user_param import Slider

from model.model import LuckVsSkillModel

def post_process_lines(ax):
    ax.set_xlabel("Simulation Step")
    ax.set_ylabel("Average True Skill")
    ax.set_title("Luck vs Skill in Short-Term Gambling")
    ax.legend()


COLORS = {
    "Top 10": "#d62728",
    "Bottom 10": "#1f77b4",
}


lineplot_component = make_plot_component(
    COLORS,
    post_process=post_process_lines,
)

model = LuckVsSkillModel()

model_params = {
    "num_agents": 200,
    "alpha": Slider("Skill impact (α)", 0.05, 0.0, 0.2, 0.01),
    "initial_wealth": 100,
    "bet_size": 1,
}

page = SolaraViz(
    model,
    components=[lineplot_component],
    model_params=model_params,
    name="Luck vs Skill: Short-Term Gambling",
)
