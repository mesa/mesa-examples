from geo_sir.agents import PersonAgent
from geo_sir.model import GeoSir
from mesa.visualization import Slider, SolaraViz, make_plot_component
from mesa_geo.visualization import make_geospace_component

model_params = {
    "pop_size": Slider("Population size", 30, 10, 100, 10),
    "init_infected": Slider("Fraction initial infection", 0.2, 0.00, 1.0, 0.05),
    "exposure_distance": Slider("Exposure distance", 500, 100, 1000, 100),
}


def infected_draw(agent):
    """Portrayal Method for canvas"""
    portrayal = {}
    if isinstance(agent, PersonAgent):
        portrayal["radius"] = "2"
    if agent.atype in ["hotspot", "infected"]:
        portrayal["color"] = "Red"
    elif agent.atype in ["safe", "susceptible"]:
        portrayal["color"] = "Green"
    elif agent.atype in ["recovered"]:
        portrayal["color"] = "Blue"
    elif agent.atype in ["dead"]:
        portrayal["color"] = "Black"
    return portrayal


model = GeoSir()
page = SolaraViz(
    model,
    name="Basic agent-based SIR model",
    model_params=model_params,
    components=[
        make_geospace_component(infected_draw, zoom=12),
        make_plot_component(["infected", "susceptible", "recovered", "dead"]),
    ],
)

page  # noqa
