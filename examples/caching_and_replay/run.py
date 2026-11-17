"""Schelling model visualization with caching and replay.

Extends the standard Schelling visualization to record and replay simulations.
"""

from pathlib import Path

import solara
from cacheablemodel import CacheableSchelling
from mesa.visualization import SolaraViz, make_plot_component, make_space_component
from mesa.visualization.utils import update_counter
from mesa_replay import CacheState
from server import agent_portrayal, get_happy_agents, model_params

# Add replay parameter to model params
model_params["replay"] = {
    "type": "Checkbox",
    "value": False,
    "label": "Replay cached run?",
}
model_params["cache_file_path"] = {
    "type": "InputText",
    "value": "./my_cache_file_path.cache",
    "label": "Cache File Path",
}


@solara.component
def get_cache_file_status(model):
    """Display cache status and instructions."""

    update_counter.get()

    cache_file = Path(model.cache_file_path)
    exists = cache_file.exists() and cache_file.is_file()

    if model._cache_state == CacheState.REPLAY:
        max_step = len(model.cache) - 1 if hasattr(model, "cache") else "unknown"
        instructions = f"Replaying cached simulation (steps 0-{max_step})  \n"
    elif model._cache_state == CacheState.RECORD:
        instructions = "Recording simulation  \n"

    file_size = ""
    if exists:
        size_bytes = cache_file.stat().st_size
        if size_bytes < 1024:
            file_size = f" ({size_bytes} bytes)"
        elif size_bytes < 1024 * 1024:
            file_size = f" ({size_bytes / 1024:.1f} KB)"
        else:
            file_size = f" ({size_bytes / (1024 * 1024):.1f} MB)"

    solara.Markdown(
        f"\n \n"
        f"---  \n"
        f"**Cache File:** `{cache_file}`{file_size}  \n"
        f"{instructions}  \n"
        f"**How to use:**  \n"
        f"• **Record:** Uncheck 'Replay', click Reset & Run  \n"
        f"• **Replay:** Check 'Replay', click Reset & Run  \n"
        f"*Cache is saved automatically when the simulation completes*"
    )


# Initialize cacheable model
model = CacheableSchelling()

# Create visualization components
space_component = make_space_component(agent_portrayal)
happy_chart = make_plot_component("happy")

# Create the Solara visualization page
Page = SolaraViz(
    model,
    components=[
        space_component,
        happy_chart,
        get_happy_agents,
        get_cache_file_status,
    ],
    model_params=model_params,
    name="Schelling Segregation Model (Cacheable)",
)
