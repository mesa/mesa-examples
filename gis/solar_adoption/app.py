import solara
from mesa.visualization import Slider, SolaraViz, make_plot_component
from mesa_geo.visualization import make_geospace_component

from model import SolarAdoption


def adoption_draw(agent):
    """Portrayal Method for canvas."""
    portrayal = {}
    if agent.has_solar:
        portrayal["color"] = "gold"
        portrayal["radius"] = 4
    else:
        portrayal["color"] = "grey"
        portrayal["radius"] = 3
    return portrayal


def raster_draw(cell):
    """Portrayal function for solar radiation."""
    val = getattr(cell, "radiation", 0)
    r = int(255 * val)
    g = int(255 * val)
    b = 0
    return {"color": f"rgba({r}, {g}, {b}, 0.5)"}


model_params = {
    "num_houses": Slider("Number of Households", 100, 10, 500, 10),
    "social_weight": Slider("Social Influence Weight", 0.3, 0.0, 1.0, 0.1),
    "economic_weight": Slider("Economic Weight (Radiation)", 0.3, 0.0, 1.0, 0.1),
}


model = SolarAdoption()
page = SolaraViz(
    model,
    name="Solar Adoption",
    model_params=model_params,
    components=[
        make_geospace_component(
            agent_portrayal=adoption_draw,
            raster_portrayal=raster_draw,
            zoom=12
        ),
        make_plot_component(["Adopted"]),
    ],
)

page  # noqa
