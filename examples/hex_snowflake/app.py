from hex_snowflake.model import HexSnowflake
from mesa.visualization import SolaraViz, make_space_component


def snowflake_portrayal(agent):
    if agent is None:
        return

    x, y = agent.cell.coordinate
    state = agent.model.state_grid[x, y]

    # State 1 is frozen (snowflake), state 0 is empty
    color = "steelblue" if state == 1 else "#F0F0F0"
    return {"color": color, "marker": "h", "size": 20}


model_params = {
    "width": 50,
    "height": 50,
}

model = HexSnowflake()

page = SolaraViz(
    model,
    components=[make_space_component(snowflake_portrayal)],
    model_params=model_params,
    name="Hex Snowflake",
)
