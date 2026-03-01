import solara
from mesa.visualization import Slider, SolaraViz, make_plot_component
from mesa_geo.visualization import make_geospace_component
from urban_growth.model import UrbanGrowth
from urban_growth.space import UrbanCell


def cell_portrayal(cell: UrbanCell) -> tuple[float, float, float, float]:
    if cell.urban:
        if cell.old_urbanized:
            return 0, 0, 255, 1
        else:
            return 255, 0, 0, 1
    else:
        return 0, 0, 0, 0


def make_plot_urbanized(model):
    return solara.Markdown(f"**Percentage Urbanized: {model.pct_urbanized:.2f}%**")


model_params = {
    "max_coefficient": 100,
    "dispersion_coefficient": Slider("dispersion_coefficient", 20, 0, 100, 1),
    "spread_coefficient": Slider("spread_coefficient", 27, 0, 100, 1),
    "breed_coefficient": Slider("breed_coefficient", 5, 0, 100, 1),
    "rg_coefficient": Slider("rg_coefficient", 10, 0, 100, 1),
    "slope_coefficient": Slider("slope_coefficient", 50, 0, 100, 1),
    "critical_slope": Slider("critical_slope", 25, 0, 100, 1),
    "road_influence": False,
}

model = UrbanGrowth()
page = SolaraViz(
    model,
    name="Urban Growth Model",
    model_params=model_params,
    components=[
        make_geospace_component(cell_portrayal, zoom=12.1),
        make_plot_component(["Percentage Urbanized"]),
        make_plot_urbanized,
    ],
)

page  # noqa
