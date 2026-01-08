import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
from mesa.visualization import SolaraViz, make_space_component
from mesa.visualization.components import PropertyLayerStyle

from .agent import AntState
from .model import AntForaging

plt.rcParams["figure.figsize"] = (10, 10)


def agent_portrayal(agent):
    """
    Portrayal for the Ant agents.
    """
    if agent.state == AntState.FORAGING:
        return {"color": "tab:red", "size": 19}
    elif agent.state == AntState.RETURNING:
        # Gold color for ants carrying food
        return {"color": "gold", "size": 17}


def property_portrayal(layer):
    """
    Portrayal for the Environment (PropertyLayers).
    """
    if layer.name == "food":
        # Dense Food clusters
        return PropertyLayerStyle(
            colormap=ListedColormap(["#00000000", "forestgreen"]),  # Transparent for 0
            vmin=0,
            vmax=1,
            alpha=0.8,
            colorbar=False,
        )

    if layer.name == "pheromone_food":
        # Greenish trails
        cmap = LinearSegmentedColormap.from_list("pher_food", ["#00000000", "lime"])
        return PropertyLayerStyle(
            colormap=cmap, vmin=0.1, vmax=10.0, alpha=0.5, colorbar=False
        )

    if layer.name == "pheromone_home":
        # Light blue trails
        cmap = LinearSegmentedColormap.from_list(
            "lightblue_grad", [(0, 0, 0, 0), "lightblue"]
        )
        return PropertyLayerStyle(
            colormap=cmap, vmin=0.01, vmax=10.0, alpha=0.6, colorbar=False
        )

    if layer.name == "home":
        # Blue nest
        return PropertyLayerStyle(
            colormap=ListedColormap(["#00000000", "darkblue"]),
            vmin=0,
            vmax=1,
            alpha=1.0,
            colorbar=False,
        )

    return None


model = AntForaging()

page = SolaraViz(
    model,
    components=[
        make_space_component(
            agent_portrayal=agent_portrayal, propertylayer_portrayal=property_portrayal
        )
    ],
    name="Hexagonal Ant Colony",
)
