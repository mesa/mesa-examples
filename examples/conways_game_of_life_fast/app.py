from mesa.visualization import SolaraViz, make_plot_component, make_space_component
from model import GameOfLifeModel

propertylayer_portrayal = {
    "cell_layer": {
        "color": "Black",
        "alpha": 1,
        "colorbar": False,
    },
}

model_params = {
    "width": {
        "type": "SliderInt",
        "value": 30,
        "label": "Width",
        "min": 5,
        "max": 60,
        "step": 1,
    },
    "height": {
        "type": "SliderInt",
        "value": 30,
        "label": "Height",
        "min": 5,
        "max": 60,
        "step": 1,
    },
    "alive_fraction": {
        "type": "SliderFloat",
        "value": 0.2,
        "label": "Cells alive",
        "min": 0,
        "max": 1,
        "step": 0.01,
    },
}

gol = GameOfLifeModel()

layer_viz = make_space_component(propertylayer_portrayal=propertylayer_portrayal)
TotalAlivePlot = make_plot_component("Cells alive")

page = SolaraViz(
    gol,
    components=[layer_viz, TotalAlivePlot],
    model_params=model_params,
    name="Game of Life Model",
)
