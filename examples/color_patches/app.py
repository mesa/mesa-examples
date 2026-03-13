"""Handles the definition of the canvas parameters and
the drawing of the model representation on the canvas.
"""

from color_patches.model import ColorPatches
from mesa.visualization import (
    SolaraViz,
    make_space_component,
)

_COLORS = [
    "Aqua",
    "Blue",
    "Fuchsia",
    "Gray",
    "Green",
    "Lime",
    "Maroon",
    "Navy",
    "Olive",
    "Orange",
    "Purple",
    "Red",
    "Silver",
    "Teal",
    "White",
    "Yellow",
]


grid_rows = 50
grid_cols = 25


def color_patch_draw(agent):
    """Portrayal function called each tick to describe how to draw a cell.

    Mesa's draw_orthogonal_grid passes agent objects to this function directly.
    We read the opinion state from model.opinion_grid (NumPy array) via
    agent.model rather than from any attribute on the agent itself.

    :param agent: the ColorCell agent at this grid position
    :return: the portrayal dictionary
    """
    if agent is None:
        raise AssertionError

    # Read coordinate and state from the model-level NumPy array.
    x, y = agent.cell.coordinate
    state = int(agent.model.opinion_grid[x, y])

    return {
        "Shape": "rect",
        "w": 1,
        "h": 1,
        "Filled": "true",
        "Layer": 0,
        "x": x,
        "y": y,
        "color": _COLORS[state],
    }


space_component = make_space_component(
    color_patch_draw,
    draw_grid=False,
)
model = ColorPatches(width=grid_rows, height=grid_cols)
page = SolaraViz(
    model,
    components=[space_component],
    model_params={"width": grid_rows, "height": grid_cols},
    name="Color Patches",
)
