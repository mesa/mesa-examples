from mesa.visualization import SolaraViz, make_space_component, make_plot_component
from mesa.visualization.user_param import Slider
import matplotlib.cm as cm
from matplotlib.colors import to_hex
from wind_driven_fire.agent import Tree
from wind_driven_fire.model import ForestFire

WIDTH = 100
HEIGHT = 100
COLORS = {"Fine": "#00AA00", "On Fire": "#880000", "Burned Out": "#000000"}

cx, cy = WIDTH // 2, HEIGHT // 2
center_9_points = [
    (x, y) 
    for x in range(cx - 1, cx + 2)  
    for y in range(cy - 1, cy + 2)  
]


def forest_fire_portrayal(agent):
    if agent is None:
        return
    
    class_name = type(agent).__name__

    # Tree
    if isinstance(agent, Tree):
        return {
            "color": COLORS[agent.condition],
            "size": 20,
            "marker": "s",
        }
    
ros_plot = make_plot_component(
    {"Rate of spread at the fire head": "blue", "Rate of spread at the fire Flank": "orange"}
)


model = ForestFire(width=100, height=100, p_spread=0.25, wind_dir=0.0, wind_strength=0.8,ignite_pos=center_9_points)
model_params = {
    "height": HEIGHT,
    "width": WIDTH,
    "p_spread": Slider("Spread probability", 0.25, 0.0, 1.0, 0.05),
    "wind_dir": Slider("Wind direction (deg)", 0.0, 0.0, 360.0, 5.0),
    "wind_strength": Slider("Wind strength", 0.8, 0.0, 1.0, 0.1),
    "ignite_pos": center_9_points #central ignite
}

space_component = make_space_component(
    forest_fire_portrayal,
    backend="matplotlib"
)

page = SolaraViz(
    model,
    components=[space_component, ros_plot],
    post_process=None,
    backend="matplotlib",
    model_params=model_params,
    portrayal_method=forest_fire_portrayal,
    name="Wind-Driven Forest Fire ",
    description="""
    **Anisotropic Fire Spread Demonstration**
    
    This example highlights how wind introduces **anisotropy** into the system.
    
    * **Visual Proof**: The blue arrow indicates wind direction. Note how the fire scar (black agents) elongates along the arrow's direction.
    * **Statistical Proof**: Observe the chart below. "Span Y" vs "Span X" shows the divergence in spread width vs height, confirming the fire is elliptical, not circular.
    """
)