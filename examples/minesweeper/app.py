import solara
from mesa.visualization import SolaraViz, make_space_component
from minesweeper.agents import MineCell
from minesweeper.model import MinesweeperModel


def agent_portrayal(agent: MineCell):
    if not agent.revealed:
        return {
            "color": "green",
            "size": 40,
        }

    if agent.cell.mine:
        return {
            "color": "red",
            "size": 40,
        }

    if agent.neighbor_mines > 0:
        return {
            "color": "lightgray",
            "text": str(agent.neighbor_mines),
            "size": 40,
        }

    return {
        "color": "lightgray",
        "size": 40,
    }


def on_cell_click(agent: MineCell):
    agent.model.reveal_cell(agent.cell)


@solara.component
def GameStatus(model):
    if model.win:
        solara.Markdown("## You Win!")
    elif model.game_over:
        solara.Markdown("## Game Over")


model_params = {
    "seed": 42,
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
        "max": 30,
        "step": 1,
    },
    "height": {
        "type": "SliderInt",
        "value": 10,
        "label": "Height",
        "min": 5,
        "max": 30,
        "step": 1,
    },
}


model = MinesweeperModel()

space = make_space_component(
    agent_portrayal=agent_portrayal,
    on_click=on_cell_click,
)

page = SolaraViz(
    model,
    components=[
        space,
        GameStatus,
    ],
    model_params=model_params,
    name="Minesweeper",
)
