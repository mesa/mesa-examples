from mesa.visualization import SolaraViz
from mesa.visualization.components.matplotlib_components import (
    make_mpl_plot_component,
    make_mpl_space_component,
)
from mesa.visualization.components.portrayal_components import AgentPortrayalStyle
from minesweeper.agents import MineCell
from minesweeper.model import MinesweeperModel


def agent_portrayal(agent: MineCell):
    if not agent.revealed:
        return AgentPortrayalStyle(
            marker="s",
            color="green",
            size=80,
        )

    if agent.cell.mine:
        return AgentPortrayalStyle(
            marker="X",
            color="red",
            size=80,
        )

    if agent.neighbor_mines > 0:
        return AgentPortrayalStyle(
            marker=f"${agent.neighbor_mines}$",
            color="black",
            size=80,
        )

    return AgentPortrayalStyle(
        marker="s",
        color="lightgray",
        size=80,
    )


model_params = {
    "seed": {"type": "InputText", "value": 42},
    "mine_density": {
        "type": "SliderFloat",
        "value": 0.15,
        "min": 0.05,
        "max": 0.4,
        "step": 0.05,
    },
    "width": {"type": "SliderInt", "value": 10, "min": 5, "max": 40},
    "height": {"type": "SliderInt", "value": 10, "min": 5, "max": 40},
}


model = MinesweeperModel()


def post_process(ax):
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])


space = make_mpl_space_component(
    agent_portrayal=agent_portrayal,
    post_process=post_process,
    draw_grid=True,
)

plot = make_mpl_plot_component(
    {
        "Revealed": "tab:blue",
        "Frontier": "tab:orange",
    }
)

page = SolaraViz(
    model,
    components=[space, plot],
    model_params=model_params,
    name="Minesweeper (Step-based)",
)
