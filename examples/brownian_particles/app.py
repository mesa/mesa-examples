import matplotlib.cm as cm
import matplotlib.colors as mcolors
from brownian_particles.model import BrownianModel, BrownianScenario
from mesa.visualization import Slider, SolaraViz
from mesa.visualization.components.matplotlib_components import SpaceMatplotlib

# color particles based on how many neighbors they have
# more neighbors = warmer color (yellow/red), fewer = cooler (blue/purple)
_cmap = cm.get_cmap("plasma")
_norm = mcolors.Normalize(vmin=0, vmax=10)


def particle_draw(agent):
    # clamp neighbor count to 0-10 range for the colormap
    nc = min(agent.n_neighbors, 10)
    rgba = _cmap(_norm(nc))
    hex_color = mcolors.to_hex(rgba)
    return {"color": hex_color, "size": 15}


model_params = {
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "n_particles": Slider(
        label="Number of Particles",
        value=80,
        min=10,
        max=300,
        step=10,
    ),
    "diffusion_rate": Slider(
        label="Diffusion Rate",
        value=0.5,
        min=0.1,
        max=3.0,
        step=0.1,
    ),
    "vision": Slider(
        label="Neighbor Detection Radius",
        value=4.0,
        min=1.0,
        max=15.0,
        step=0.5,
    ),
}


def make_model(**kwargs):
    scenario = BrownianScenario(
        n_particles=kwargs.get("n_particles", 80),
        diffusion_rate=kwargs.get("diffusion_rate", 0.5),
        vision=kwargs.get("vision", 4.0),
    )
    return BrownianModel(scenario=scenario)


page = SolaraViz(
    make_model,
    components=[SpaceMatplotlib(particle_draw)],
    model_params=model_params,
    name="Brownian Particles",
)
page  # noqa
