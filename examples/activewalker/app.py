
from mesa.visualization import SolaraViz, SpaceRenderer, Slider, make_space_component
from mesa.visualization.components import AgentPortrayalStyle,  PropertyLayerStyle
import solara
from matplotlib.figure import Figure
from mesa.visualization.utils import update_counter
from matplotlib.figure import Figure
from model import ActiveWalkerModel
from agent import StopsAgent

parameters = {
    'stops': [(5, 5), (35, 5), (20, 35)], 
    'population_size': 80,      
    'width': 40,
    'height': 40,
    'speed_mean': 1.0,          
    
    'default_value': 0,
    'max_value': 10,
    
    'print_strength': 5.0,      
    'trail_dies_in': 2000,      
    
    'vision': 4,                
    'resolution': 2,
    'rng': None
}

model = ActiveWalkerModel(**parameters)


@solara.component
def TrailHeatmap(model):
    update_counter.get()
    fig = Figure()
    ax = fig.subplots()
    if hasattr(model, 'G_layer'):
        data = model.G_layer.V.copy()

        im = ax.imshow(data, cmap='magma', interpolation='nearest', origin='lower', aspect='auto')
        
        fig.colorbar(im, ax=ax, label="Pheromone Intensity")
        
        ax.set_title(f"Trail Intensity (Step {model.steps})")
        ax.set_xlabel("X Coordinate")
        ax.set_ylabel("Y Coordinate")

    solara.FigureMatplotlib(fig)

@solara.component
def Trail(model):
    update_counter.get()
    fig = Figure()
    ax = fig.subplots()
    if hasattr(model, 'G_layer'):
        data = model.G_layer.data.copy()

        im = ax.imshow(data, cmap='Greens', interpolation='nearest', origin='lower', aspect='auto')
        
        fig.colorbar(im, ax=ax, label="Pheromone Intensity")
        
        ax.set_title(f"Trail (Step {model.steps})")
        ax.set_xlabel("X Coordinate")
        ax.set_ylabel("Y Coordinate")

    solara.FigureMatplotlib(fig)


def agent_portrayal(agent):
    if isinstance(agent, StopsAgent):
        return AgentPortrayalStyle(
            size=200,      
            marker="house.png",
            zorder=100
        )
    
    boid_style = AgentPortrayalStyle(
        size=20, marker='o', color='red'
    )
    if agent.reached:
        boid_style.update(("color", "green"), ("size", 30))

    return boid_style

model_params = {
    "population_size": Slider(
        label="Number",
        value=80,
        min=10,
        max=200,
        step=10
    ),
    "speed_mean": Slider(
        label="speed",
        value=1.0,
        min=0.1,
        max=2.0,
        step=0.1
    ),
    "default_value": Slider(
        label="min trail strength",
        value=0,
        min=0,
        max=1.0,
        step=0.1
    ),
    "max_value": Slider(
        label="max trail strength",
        value=10,
        min=1,
        max=50,
        step=1
    ),
    "print_strength": Slider(
        label="agent print strength",
        value=5,
        min=1,
        max=50,
        step=5
    ),     
    "trail_dies_in": Slider(
        label="trail dies in",
        value=2000,
        min=100,
        max=2001,
        step=100
    ),
    "vision": Slider(
        label="vision",
        value=4,
        min=2,
        max=10,
        step=1
    ),                  
    "resolution": Slider(
        label="resolution of trail grid",
        value=2,
        min=1,
        max=10,
        step=1
    ),
    "rng": None,
    "stops": [(5, 5), (35, 5), (20, 35)], 
    "width": 40,
    "height": 40
}


renderer = (
    SpaceRenderer(
        model,
        backend="matplotlib",
    )
)
renderer.draw_agents(agent_portrayal)

page = SolaraViz(
    model,
    renderer,
    components=[TrailHeatmap, Trail],
    model_params=model_params,
    name="Actice Walker Model",
)

page