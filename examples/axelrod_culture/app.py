import hashlib

import numpy as np
import solara
from matplotlib.figure import Figure

from mesa.visualization import SolaraViz, make_plot_component
from axelrod_culture.model import AxelrodModel, number_of_cultural_regions


def culture_to_color(culture):
    key = str(culture).encode()
    h = hashlib.sha256(key).hexdigest()
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255)


def make_culture_grid(model):
    fig = Figure(figsize=(5, 5))
    fig.subplots_adjust(left=0.05, right=0.95, top=0.92, bottom=0.05)
    ax = fig.add_subplot(111)
    grid = np.zeros((model.height, model.width, 3))
    for agent in model.agents:
        x, y = int(agent.cell.coordinate[0]), int(agent.cell.coordinate[1])
        grid[y][x] = culture_to_color(agent.culture)
    ax.imshow(grid, origin="lower", interpolation="nearest")
    ax.set_title(f"Cultural Regions: {number_of_cultural_regions(model)}", fontsize=11)
    ax.set_xticks([])
    ax.set_yticks([])
    return solara.FigureMatplotlib(fig)


RegionsPlot = make_plot_component({"Cultural Regions": "#e63946"})

model_params = {
    "rng": {
        "type": "SliderInt",
        "value": 42,
        "label": "Random Seed",
        "min": 0,
        "max": 1000,
        "step": 1,
    },
    "width": {"type": "SliderInt", "value": 10, "label": "Grid Width", "min": 5, "max": 20, "step": 1},
    "height": {"type": "SliderInt", "value": 10, "label": "Grid Height", "min": 5, "max": 20, "step": 1},
    "f": {"type": "SliderInt", "value": 3, "label": "Features (F)", "min": 2, "max": 10, "step": 1},
    "q": {"type": "SliderInt", "value": 3, "label": "Traits per feature (Q)", "min": 2, "max": 15, "step": 1},
}

model = AxelrodModel()

page = SolaraViz(
    model,
    components=[make_culture_grid, RegionsPlot],
    model_params=model_params,
    name="Axelrod Culture Model",
)
page  