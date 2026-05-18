from agents import Household
from mesa.visualization import Slider, SolaraViz, make_plot_component
from mesa_geo.visualization import make_geospace_component
from model import SolarAdoption


def solar_portrayal(agent):
    """Portrayal function for households and solar radiation cells."""
    if isinstance(agent, Household):
        portrayal = {}
        if agent.has_solar:
            portrayal["color"] = "gold"
            portrayal["radius"] = 4
        else:
            portrayal["color"] = "grey"
            portrayal["radius"] = 3
        return portrayal
    else:
        # It's a Raster Cell
        val = getattr(agent, "radiation", 0)
        r = int(255 * val)
        g = int(255 * val)
        b = 0
        return (r, g, b, 128)


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
        make_geospace_component(solar_portrayal, zoom=9),
        make_plot_component(["Adopted"]),
    ],
)

page  # noqa
