from mesa.visualization import SolaraViz
from mesa.visualization.components.matplotlib_components import make_mpl_space_component
from termites.model import TermiteModel

wood_chip_portrayal = {
    "woodcell": {
        "color": "blue",
        "alpha": 0.6,
        "colorbar": False,
        "vmin": 0,
        "vmax": 2,
    },
}


def agent_portrayal(agent):
    return {
        "marker": ">",
        "color": "red" if agent.has_woodchip else "black",
        "size": 10,
    }


model_params = {
    "rng": {
        "type": "InputText",
        "value": 42,
        "label": "rng",
    },
    "num_termites": {
        "type": "SliderInt",
        "value": 100,
        "label": "No. of Termites",
        "min": 10,
        "max": 1000,
        "step": 1,
    },
    "wood_chip_density": {
        "type": "SliderFloat",
        "value": 0.1,
        "label": "Wood Chip Density",
        "min": 0.01,
        "max": 1,
        "step": 0.1,
    },
    "width": {
        "type": "SliderInt",
        "value": 100,
        "label": "Width",
        "min": 10,
        "max": 500,
        "step": 1,
    },
    "height": {
        "type": "SliderInt",
        "value": 100,
        "label": "Height",
        "min": 10,
        "max": 500,
        "step": 1,
    },
}

model = TermiteModel()


def post_process(ax):
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])


woodchips_space = make_mpl_space_component(
    agent_portrayal=agent_portrayal,
    propertylayer_portrayal=wood_chip_portrayal,
    post_process=post_process,
    draw_grid=False,
)

page = SolaraViz(
    model,
    components=[woodchips_space],
    model_params=model_params,
    name="Termites Model",
)
