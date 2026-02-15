from mesa.examples.advanced.wolf_sheep.agents import GrassPatch, Sheep, Wolf
from mesa.examples.advanced.wolf_sheep.model import WolfSheep
from mesa.experimental.devs import ABMSimulator
from mesa.visualization import (
    Slider,
    SolaraViz,
    make_plot_component,
    make_space_component,
)
from model import WolfSheepRL
from ray import tune
from ray.rllib.algorithms.algorithm import Algorithm

model_params = {
    "width": 20,
    "height": 20,
    "initial_sheep": 100,
    "initial_wolves": 25,
    "sheep_reproduce": 0.04,
    "wolf_reproduce": 0.05,
    "wolf_gain_from_food": 20,
    "grass": True,
    "grass_regrowth_time": 30,
    "sheep_gain_from_food": 4,
    "seed": 42,
    "simulator": ABMSimulator(),
    "vision": 4,
    "model_path": None,
}


class WolfSheepServer(WolfSheepRL):
    def __init__(self, **model_params):
        super().__init__(**model_params)

        def env_creator(_):
            return WolfSheepRL(**model_params)

        tune.register_env("WorldSheepModel-v0", env_creator)
        self.iteration = 0
        # Load the model from checkpoint
        checkpoint_path = self.model_path
        algo = Algorithm.from_checkpoint(checkpoint_path)
        self.wolf_policy = algo.get_policy("policy_wolf")
        self.sheep_policy = algo.get_policy("policy_sheep")


def wolf_sheep_portrayal(agent):
    if agent is None:
        return

    portrayal = {
        "size": 25,
    }

    if isinstance(agent, Wolf):
        portrayal["color"] = "tab:red"
        portrayal["marker"] = "o"
        portrayal["zorder"] = 2
    elif isinstance(agent, Sheep):
        portrayal["color"] = "tab:cyan"
        portrayal["marker"] = "o"
        portrayal["zorder"] = 2
    elif isinstance(agent, GrassPatch):
        if agent.fully_grown:
            portrayal["color"] = "tab:green"
        else:
            portrayal["color"] = "tab:brown"
        portrayal["marker"] = "s"
        portrayal["size"] = 75

    return portrayal


model_params = {
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "grass": {
        "type": "Select",
        "value": True,
        "values": [True, False],
        "label": "grass regrowth enabled?",
    },
    "grass_regrowth_time": Slider("Grass Regrowth Time", 20, 1, 50),
    "initial_sheep": Slider("Initial Sheep Population", 100, 10, 300),
    "sheep_reproduce": Slider("Sheep Reproduction Rate", 0.04, 0.01, 1.0, 0.01),
    "initial_wolves": Slider("Initial Wolf Population", 10, 5, 100),
    "wolf_reproduce": Slider(
        "Wolf Reproduction Rate",
        0.05,
        0.01,
        1.0,
        0.01,
    ),
    "wolf_gain_from_food": Slider("Wolf Gain From Food Rate", 20, 1, 50),
    "sheep_gain_from_food": Slider("Sheep Gain From Food", 4, 1, 10),
}


def post_process_space(ax):
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])


def post_process_lines(ax):
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.9))


space_component = make_space_component(
    wolf_sheep_portrayal, draw_grid=False, post_process=post_process_space
)
lineplot_component = make_plot_component(
    {"Wolves": "tab:orange", "Sheep": "tab:cyan", "Grass": "tab:green"},
    post_process=post_process_lines,
)

simulator = ABMSimulator()
model = WolfSheep(simulator=simulator, grass=True)

page = SolaraViz(
    model,
    components=[space_component, lineplot_component],
    model_params=model_params,
    name="Wolf Sheep",
    simulator=simulator,
)
page  # noqa
