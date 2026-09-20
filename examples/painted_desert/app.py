from matplotlib.colors import ListedColormap
from mesa.visualization import SolaraViz, make_space_component
from mesa.visualization.components import AgentPortrayalStyle, PropertyLayerStyle
from painted_desert.model import ChipCollectorModel

# Centralized color mapping for easy modification
CHIP_COLOR_MAP = {
    0: "black",  # Background/empty patches
    -1: "white",  # Agents not carrying chips
    1: "grey",
    2: "red",
    3: "orange",
    4: "brown",
    5: "yellow",
    6: "green",
    7: "lime",
    8: "turquoise",
    9: "cyan",
    10: "navy",
    11: "blue",
    12: "violet",
    13: "magenta",
    14: "pink",
}


def agent_portrayal(agent):
    """Define how chip collector agents appear in the visualization."""
    if agent is None:
        return None

    # visual_color can be -1 (int) when not carrying, or chip_color (int) when carrying
    visual_color = agent.visual_color
    color = CHIP_COLOR_MAP.get(visual_color, "black")

    return AgentPortrayalStyle(color=color, size=50, edgecolors="black")


def property_portrayal(layer):
    """Define how property layers (patch colors) appear in the visualization."""
    if layer.name != "pcolor":
        return None

    color_list = [CHIP_COLOR_MAP.get(i, "gray") for i in range(15)]
    cmap = ListedColormap(color_list)

    return PropertyLayerStyle(
        colormap=cmap,
        vmin=0,
        vmax=14,  # Max expected value
        alpha=1.0,
        colorbar=False,
    )


model_params = {
    "width": {
        "type": "SliderInt",
        "value": 40,
        "label": "Grid width:",
        "min": 20,
        "max": 100,
        "step": 5,
    },
    "height": {
        "type": "SliderInt",
        "value": 40,
        "label": "Grid height:",
        "min": 20,
        "max": 100,
        "step": 5,
    },
    "density": {
        "type": "SliderFloat",
        "value": 45,
        "label": "Chip density (%):",
        "min": 10,
        "max": 90,
        "step": 5,
    },
    "number": {
        "type": "SliderInt",
        "value": 150,
        "label": "Number of agents:",
        "min": 50,
        "max": 250,
        "step": 10,
    },
    "colors": {
        "type": "SliderInt",
        "value": 4,
        "label": "Number of chip colors:",
        "min": 2,
        "max": 14,
        "step": 1,
    },
}

# Create initial model instance
woodchip_model = ChipCollectorModel(
    width=40, height=40, density=45, number=150, colors=4, seed=42
)

# Create visualization page
page = SolaraViz(
    woodchip_model,
    components=[
        make_space_component(
            agent_portrayal=agent_portrayal, propertylayer_portrayal=property_portrayal
        )
    ],
    model_params=model_params,
    name="Painted Desert Challenge Model",
)
