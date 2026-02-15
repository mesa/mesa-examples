import solara
from mesa.visualization import Slider, SolaraViz, make_plot_component
from mesa_geo.visualization import make_geospace_component
from model import GeoSchelling


def make_plot_happiness(model):
    return solara.Markdown(f"**Happy agents: {model.happy}**")


model_params = {
    "density": Slider("Agent density", 0.6, 0.1, 1.0, 0.1),
    "minority_pc": Slider("Fraction minority", 0.2, 0.00, 1.0, 0.05),
    "export_data": False,
}


def schelling_draw(agent):
    """Portrayal Method for canvas"""
    portrayal = {}
    if agent.atype is None:
        portrayal["color"] = "Grey"
    elif agent.atype == 0:
        portrayal["color"] = "Red"
    else:
        portrayal["color"] = "Blue"
    return portrayal


model = GeoSchelling()
page = SolaraViz(
    model,
    name="GeoSchelling",
    model_params=model_params,
    components=[
        make_geospace_component(schelling_draw, zoom=4),
        make_plot_component(["happy"]),
        make_plot_happiness,
    ],
)

page  # noqa
