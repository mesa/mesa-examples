from mesa.visualization import SolaraViz, make_space_component
from shape_example.model import ShapeExample, Walker


def agent_portrayal(agent):
    if isinstance(agent, Walker):
        return {
            "color": "tab:green",
            "size": 50,
            "marker": "^",
        }


model = ShapeExample()

page = SolaraViz(
    model,
    components=[make_space_component(agent_portrayal=agent_portrayal)],
    name="Shape Model Example",
)
