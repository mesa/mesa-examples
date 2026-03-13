from hex_snowflake.cell import Cell
from hex_snowflake.model import HexSnowflake
from mesa.visualization import SolaraViz, make_space_component


def agent_portrayal(agent):
    if agent is None:
        return

    if isinstance(agent, Cell):
        color = "tab:green" if agent.state == Cell.ALIVE else "tab:grey"
        return {"color": color, "size": 20}


model = HexSnowflake()

page = SolaraViz(
    model,
    components=[make_space_component(agent_portrayal=agent_portrayal)],
    name="Hex Snowflake",
)
