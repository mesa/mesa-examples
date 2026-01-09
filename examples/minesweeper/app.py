from mesa.visualization import SolaraViz
from mesa.visualization.components.matplotlib_components import (
    make_mpl_space_component,
)
from minesweeper.agents import MineCell
from minesweeper.model import MinesweeperModel

mine_layer_portrayal = {
    "mine": {
        "color": "black",
        "alpha": 0.8,
        "colorbar": False,
        "vmin": 0,
        "vmax": 1,
    }
}


def agent_portrayal(agent: MineCell):
    if agent.revealed:
        if agent.cell.mine:
            return {
                "marker": "X",
                "color": "red",
                "size": 80,
            }
        else:
            return {
                "marker": f"${agent.neighbor_mines}$"
                if agent.neighbor_mines > 0
                else "s",
                "color": "lightgray",
                "size": 80,
            }
    else:
        return {
            "marker": "s",
            "color": "green",
            "size": 80,
        }


model_params = {
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Seed",
    },
    "mine_density": {
        "type": "SliderFloat",
        "value": 0.15,
        "label": "Mine Density",
        "min": 0.05,
        "max": 0.4,
        "step": 0.05,
    },
    "width": {
        "type": "SliderInt",
        "value": 10,
        "label": "Width",
        "min": 5,
        "max": 40,
        "step": 1,
    },
    "height": {
        "type": "SliderInt",
        "value": 10,
        "label": "Height",
        "min": 5,
        "max": 40,
        "step": 1,
    },
}

model = MinesweeperModel()


def post_process(ax):
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])


minesweeper_space = make_mpl_space_component(
    agent_portrayal=agent_portrayal,
    propertylayer_portrayal=mine_layer_portrayal,
    post_process=post_process,
    draw_grid=True,
)

page = SolaraViz(
    model,
    components=[minesweeper_space],
    model_params=model_params,
    name="Minesweeper (Discrete Space Model)",
)
