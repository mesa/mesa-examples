from mesa.visualization import SolaraViz, make_plot_component, make_space_component
from mesa.visualization.user_param import Slider
from wolf_sheep.agents import GrassPatch, Sheep, Wolf
from wolf_sheep.model import WolfSheep


def wolf_sheep_portrayal(agent):
    if agent is None:
        return

    if isinstance(agent, Wolf):
        return {"color": "#AA0000", "size": 50, "zorder": 3}
    elif isinstance(agent, Sheep):
        return {"color": "#AAAAAA", "size": 40, "zorder": 2}
    elif isinstance(agent, GrassPatch):
        color = "#00AA00" if agent.fully_grown else "#8B4513"
        return {"color": color, "size": 120, "marker": "s", "zorder": 1}


def post_process_space(ax):
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])


def post_process_lines(ax):
    ax.set_ylabel("Population")
    ax.legend(loc="upper right")


space_component = make_space_component(
    wolf_sheep_portrayal,
    draw_grid=False,
    post_process=post_process_space,
)

lineplot_component = make_plot_component(
    {"Wolves": "#AA0000", "Sheep": "#AAAAAA", "Grass": "#00AA00"},
    post_process=post_process_lines,
)

model_params = {
    "rng": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "grass": {
        "type": "Select",
        "value": True,
        "values": [True, False],
        "label": "Enable grass regrowth",
    },
    "initial_sheep": Slider("Initial Sheep", 100, 10, 300),
    "initial_wolves": Slider("Initial Wolves", 25, 5, 100),
    "sheep_reproduce": Slider("Sheep Reproduction Rate", 0.04, 0.01, 1.0, 0.01),
    "wolf_reproduce": Slider("Wolf Reproduction Rate", 0.05, 0.01, 1.0, 0.01),
    "wolf_gain_from_food": Slider("Wolf Energy from Food", 20, 1, 50),
    "sheep_gain_from_food": Slider("Sheep Energy from Grass", 4, 1, 20),
    "grass_regrowth_time": Slider("Grass Regrowth Time", 30, 1, 100),
}

model = WolfSheep()

page = SolaraViz(
    model,
    components=[space_component, lineplot_component],
    model_params=model_params,
    name="Wolf-Sheep Predation",
)
