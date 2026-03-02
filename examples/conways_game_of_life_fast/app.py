import matplotlib.pyplot as plt
import solara
from mesa.visualization import SolaraViz, make_plot_component
from model import GameOfLifeModel


def make_grid_component():
    @solara.component
    def GridComponent(model):
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.imshow(
            model.cell_layer.data.T,
            cmap="binary",
            interpolation="nearest",
            origin="lower",
        )
        ax.set_axis_off()
        plt.tight_layout()
        solara.FigureMatplotlib(fig)
        plt.close(fig)
    return GridComponent


model_params = {
    "width": {"type": "SliderInt", "value": 30, "label": "Width", "min": 5, "max": 60, "step": 1},
    "height": {"type": "SliderInt", "value": 30, "label": "Height", "min": 5, "max": 60, "step": 1},
    "alive_fraction": {"type": "SliderFloat", "value": 0.2, "label": "Cells alive", "min": 0, "max": 1, "step": 0.01},
}

gol = GameOfLifeModel()

GridView = make_grid_component()
TotalAlivePlot = make_plot_component("Cells alive")

page = SolaraViz(
    gol,
    components=[GridView, TotalAlivePlot],
    model_params=model_params,
    name="Game of Life Model",
)