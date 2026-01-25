import solara
from geo_schelling_points.agents import PersonAgent, RegionAgent
from geo_schelling_points.model import GeoSchellingPoints
from mesa.visualization import Slider, SolaraViz, make_plot_component
from mesa_geo.visualization import make_geospace_component


def make_plot_happiness(model):
    return solara.Markdown(f"**Happy agents: {model.happy}**")


model_params = {
    "red_percentage": Slider("% red", 0.5, 0.00, 1.0, 0.05),
    "similarity_threshold": Slider("% similar wanted", 0.5, 0.00, 1.0, 0.05),
}


def schelling_draw(agent):
    portrayal = {}
    if isinstance(agent, RegionAgent):
        if agent.red_cnt > agent.blue_cnt:
            portrayal["color"] = "Red"
        elif agent.red_cnt < agent.blue_cnt:
            portrayal["color"] = "Blue"
        else:
            portrayal["color"] = "Grey"
    elif isinstance(agent, PersonAgent):
        portrayal["radius"] = 1
        portrayal["shape"] = "circle"
        portrayal["color"] = "Red" if agent.is_red else "Blue"
    return portrayal


model = GeoSchellingPoints()
page = SolaraViz(
    model,
    name="GeoSchellingPoints",
    model_params=model_params,
    components=[
        make_geospace_component(schelling_draw, zoom=4),
        make_plot_component(["happy", "unhappy"]),
        make_plot_happiness,
    ],
)

page  # noqa
