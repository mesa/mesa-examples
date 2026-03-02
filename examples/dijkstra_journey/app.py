from mesa.visualization import SolaraViz
from dijkstra_journey.model import Dijkstra_JourneyModel


def circle_portrayal_example(agent):
    return {
        "size": 40,
        "color": "tab:red",
        "Layer": 1,
        "Shape": "circle",
    }


model_params = {
    "num_agents": 10,
    "width": 10,
    "height": 10,
}

page = SolaraViz(
    model_class=Dijkstra_JourneyModel,
    model_params=model_params,
    agent_portrayal=circle_portrayal_example,
    measures=["num_agents"],
)

page
