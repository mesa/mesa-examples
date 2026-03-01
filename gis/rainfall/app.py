from mesa.visualization import Slider, SolaraViz, make_plot_component
from mesa_geo.visualization import make_geospace_component
from rainfall.model import Rainfall
from rainfall.space import LakeCell

model_params = {
    "rain_rate": Slider("rain rate", 500, 0, 500, 5),
    "water_height": Slider("water height", 5, 1, 5, 1),
    "num_steps": Slider("total number of steps", 20, 1, 100, 1),
    "export_data": False,
}


def cell_portrayal(cell: LakeCell) -> tuple[float, float, float, float]:
    if cell.water_level == 0:
        return cell.elevation, cell.elevation, cell.elevation, 1
    else:
        # return a blue color gradient based on the normalized water level
        # from the lowest water level colored as RGBA: (74, 141, 255, 1)
        # to the highest water level colored as RGBA: (0, 0, 255, 1)
        return (
            (1 - cell.water_level_normalized) * 74,
            (1 - cell.water_level_normalized) * 141,
            255,
            1,
        )


model = Rainfall()
page = SolaraViz(
    model,
    name="Rainfall Model",
    model_params=model_params,
    components=[
        make_geospace_component(cell_portrayal, zoom=11),
        make_plot_component(
            ["Total Amount of Water", "Total Contained", "Total Outflow"]
        ),
    ],
)

page  # noqa
