import sys

from mesa.visualization import Slider, SolaraViz, make_plot_component
from mesa_geo.visualization import make_geospace_component
from src.model.model import AgentsAndNetworks
from src.visualization.utils import agent_draw, make_plot_clock


def parse_args():
    campus = "ub"
    if "--campus" in sys.argv:
        campus = sys.argv[sys.argv.index("--campus") + 1]
    return campus


if __name__ == "__main__":
    campus = parse_args()

    if campus == "ub":
        data_file_prefix = "UB"
    elif campus == "gmu":
        data_file_prefix = "Mason"
    else:
        raise ValueError("Invalid campus name. Choose from ub or gmu.")

    campus_params = {
        "ub": {"data_crs": "epsg:4326", "commuter_speed": 0.5, "zoom": 14},
        "gmu": {"data_crs": "epsg:2283", "commuter_speed": 0.4, "zoom": 16},
    }
    model_params = {
        "campus": campus,
        "data_crs": campus_params[campus]["data_crs"],
        "buildings_file": f"data/{campus}/{data_file_prefix}_bld.zip",
        "walkway_file": f"data/{campus}/{data_file_prefix}_walkway_line.zip",
        "lakes_file": f"data/{campus}/hydrop.zip",
        "rivers_file": f"data/{campus}/hydrol.zip",
        "driveway_file": f"data/{campus}/{data_file_prefix}_Rds.zip",
        "output_dir": "outputs",
        "show_walkway": True,
        "show_lakes_and_rivers": True,
        "show_driveway": True,
        "num_commuters": Slider(
            "Number of Commuters", value=50, min=10, max=150, step=10
        ),
        "commuter_speed": Slider(
            "Commuter Walking Speed (m/s)",
            value=campus_params[campus]["commuter_speed"],
            min=0.1,
            max=1.5,
            step=0.1,
        ),
    }
    model = AgentsAndNetworks()
    page = SolaraViz(
        model,
        name="Agents and Networks",
        model_params=model_params,
        components=[
            make_geospace_component(agent_draw, zoom=campus_params[campus]["zoom"]),
            make_plot_clock,
            make_plot_component(["status_home", "status_work", "status_traveling"]),
            make_plot_component(["friendship_home", "friendship_work"]),
        ],
    )

    page  # noqa
