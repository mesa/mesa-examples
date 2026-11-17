from mesa.visualization import SolaraViz, make_space_component
from model import EnergyModel


def agent_portrayal(agent):
    """Visual representation of agent based on energy level."""

    if agent.energy > agent.LOW_ENERGY_THRESHOLD + 2:
        color = "#2ecc71"  # high energy (green)
    elif agent.energy > agent.LOW_ENERGY_THRESHOLD:
        color = "#f1c40f"  # medium energy (yellow)
    else:
        color = "#e74c3c"  # low energy (red)

    return {
        "color": color,
        "size": 40,
    }


# Allow easy parameter tweaking
model = EnergyModel(
    n=20,
    width=10,
    height=10,
)

page = SolaraViz(
    model,
    components=[
        make_space_component(agent_portrayal),
    ],
)

__all__ = ["page"]
