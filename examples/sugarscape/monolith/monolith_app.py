from mesa.visualization import Slider, SolaraViz, SpaceRenderer, make_plot_component
from mesa.visualization.components import AgentPortrayalStyle, PropertyLayerStyle
from monolith_model import SugarscapeMonolith


def agent_portrayal(agent):
    color_map = {
        "survive": "black",
        "gather_sugar": "green",
        "gather_spice": "orange",
        "seek_trade": "purple",
        "default": "blue",
    }

    return AgentPortrayalStyle(
        x=agent.cell.coordinate[0],
        y=agent.cell.coordinate[1],
        color=color_map.get(agent.active_drive, "gray"),
        marker="o",
        size=10,
        zorder=1,
    )


def property_layer_portrayal(layer):
    if layer == "sugar":
        return PropertyLayerStyle(
            color="blue", alpha=0.8, colorbar=True, vmin=0, vmax=10
        )
    return PropertyLayerStyle(color="red", alpha=0.8, colorbar=True, vmin=0, vmax=10)


def post_process(chart):
    chart = chart.properties(width=400, height=400)
    return chart


model_params = {
    "rng": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "width": 50,
    "height": 50,
    # Population parameters
    "initial_population": Slider(
        "Initial Population", value=200, min=50, max=500, step=10
    ),
    # Agent endowment parameters
    "endowment_min": Slider("Min Initial Endowment", value=25, min=5, max=30, step=1),
    "endowment_max": Slider("Max Initial Endowment", value=50, min=30, max=100, step=1),
    # Metabolism parameters
    "metabolism_min": Slider("Min Metabolism", value=1, min=1, max=3, step=1),
    "metabolism_max": Slider("Max Metabolism", value=5, min=3, max=8, step=1),
    # Vision parameters
    "vision_min": Slider("Min Vision", value=1, min=1, max=3, step=1),
    "vision_max": Slider("Max Vision", value=5, min=3, max=8, step=1),
    # Trade parameter
    "enable_trade": {"type": "Checkbox", "value": True, "label": "Enable Trading"},
}

model = SugarscapeMonolith()

# Here, the renderer uses the Altair backend, while the plot components
# use the Matplotlib backend.
# Both can be mixed and matched to enhance the visuals of your model.
renderer = (
    SpaceRenderer(model, backend="altair")
    .setup_agents(agent_portrayal)
    .setup_propertylayer(property_layer_portrayal)
)
# Specifically, avoid drawing the grid to hide the grid lines.
renderer.draw_agents()
renderer.draw_propertylayer()

renderer.post_process = post_process

# Note: It is advised to switch the pages after pausing the model
# on the Solara dashboard.
page = SolaraViz(
    model,
    renderer,
    components=[
        make_plot_component("#Traders", page=1),
        make_plot_component("Price", page=1),
        make_plot_component("Survive", page=2),
        make_plot_component("Gather Sugar", page=2),
        make_plot_component("Gather Spice", page=2),
        make_plot_component("Seek Trade", page=2),
        make_plot_component("Default", page=2),
    ],
    model_params=model_params,
    name="Sugarscape {G1, M, T}",
    play_interval=150,
)
page  # noqa
