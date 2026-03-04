"""handles the definition of the canvas parameters and
the drawing of the model representation on the canvas
"""

# import webbrowser
from color_patches.model import ColorPatches
from mesa.visualization import (
    SolaraViz,
    make_space_component,
)
from mesa.visualization.user_param import (
    Slider,
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
cell_size = 10
canvas_width = grid_rows * cell_size
canvas_height = grid_cols * cell_size


def color_patch_draw(cell):
    """This function is registered with the visualization server to be called
    each tick to indicate how to draw the cell in its current state.

    :param cell:  the cell in the simulation

    :return: the portrayal dictionary.
    """
    if cell is None:
        return
    return {
        "color": _COLORS[cell.state],
        "size": 100,
    }


space_component = make_space_component(
    color_patch_draw,
    draw_grid=False,
)
model = ColorPatches()
model_params = {
    "width": Slider(
        "Grid Width",
        grid_rows,
        5,
        100,
    ),
    "height": Slider(
        "Grid Height", 
        grid_cols,
        5,
        100,
    ),
}

page = SolaraViz(
    model,
    components=[space_component],
    model_params=model_params,
    name="Color Patches",
)
