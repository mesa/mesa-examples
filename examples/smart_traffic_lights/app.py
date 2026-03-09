import mesa
from mesa.visualization import SolaraViz, make_plot_component, make_space_component
from typing import Dict, Any
from smart_traffic_lights.agents import (
    TrafficLightAgent,
    CarAgent,
    LightState,
    Direction,
)
from smart_traffic_lights.model import TrafficModel


def traffic_portrayal(agent: mesa.Agent) -> Dict[str, Any]:
    """
    Determines how agents are drawn on the grid.

    - Cars: Blue for East, Purple for North.
    - Lights: Circle markers, Red or Green based on state.
    - Controller: Hidden (has no position).
    """

    if isinstance(agent, TrafficLightAgent):
        return {
            "color": "tab:green" if agent.state == LightState.GREEN else "tab:red",
            "marker": "o",  # Circle for lights
            "size": 100,
            "zorder": 1,  # Ensure lights are drawn above cars
            "alpha": 1.0,
        }
    if isinstance(agent, CarAgent):
        return {
            "color": "tab:blue" if agent.direction == Direction.EAST else "tab:purple",
            "marker": "s",  # Square for cars
            "zorder": 0,  # Ensure lights are drawn above cars
            "size": 40,
        }
    return {}


# Define interactive parameters for Solara UI
model_params = {
    "width": mesa.visualization.Slider(
        label="Width of the grid", value=20, min=5, max=40, step=1
    ),
    "height": mesa.visualization.Slider(
        label="Height of the grid", value=20, min=5, max=40, step=1
    ),
    "num_cars_east": mesa.visualization.Slider(
        label="Number of cars going east", value=8, min=1, max=20, step=1
    ),
    "num_cars_north": mesa.visualization.Slider(
        label="Number of cars going north", value=8, min=1, max=20, step=1
    ),
    "smart_lights": mesa.visualization.Slider(
        label="Smart Lights (0=Off, 1=On)", value=1, min=0, max=1, step=1
    ),
}

# Create the Grid View
space_component = make_space_component(traffic_portrayal)

# Create the Wait Time Chart
wait_time_chart = make_plot_component({"Total_Red_Light_Wait_Time": "tab:red"})

initial_model = TrafficModel()

# Instantiate the Solara Visualization Page
app = SolaraViz(
    model=initial_model,
    model_params=model_params,
    components=[
        space_component,
        wait_time_chart,
    ],
    name="Smart Traffic Simulation",
)


app
