import solara
from mesa.visualization import SolaraViz

from .model import OpinionModel


def make_plot(model):
    # A simple placeholder for your opinion chart
    return solara.Markdown("### Opinion Dynamics Chart (WIP)")


page = SolaraViz(
    OpinionModel,
    components=[make_plot],
    name="Reactive LLM Opinion Model",
)
