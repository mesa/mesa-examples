import solara
from charts.agents import Person
from charts.model import Charts
from mesa.visualization import SolaraViz, make_plot_component, make_space_component
from mesa.visualization.components import AgentPortrayalStyle
from mesa.visualization.user_param import Slider

# Colors - same palette as the original server.py (Matplotlib tab10)
RICH_COLOR = "#2ca02c"  # green
POOR_COLOR = "#d62728"  # red
MID_COLOR = "#1f77b4"  # blue


def agent_portrayal(agent):
    """
    Returns AgentPortrayalStyle (Mesa 3.x) instead of a dict.
    Color encodes wealth class:
      green -> savings > rich_threshold  (rich)
      red   -> loans > 10               (poor)
      blue  -> everything else          (middle class)
    """
    if not isinstance(agent, Person):
        return AgentPortrayalStyle()

    color = MID_COLOR

    if agent.savings > agent.model.rich_threshold:
        color = RICH_COLOR
    if agent.loans > 10:
        color = POOR_COLOR

    return AgentPortrayalStyle(color=color, size=20, marker="o")


model_params = {
    "init_people": Slider(label="People", value=25, min=1, max=200, step=1),
    "rich_threshold": Slider(label="Rich Threshold", value=10, min=1, max=20, step=1),
    "reserve_percent": Slider(label="Reserves (%)", value=50, min=1, max=100, step=1),
}

SpaceGraph = make_space_component(agent_portrayal)

WealthClassChart = make_plot_component(
    {"Rich": RICH_COLOR, "Poor": POOR_COLOR, "Middle Class": MID_COLOR}
)

MoneySupplyChart = make_plot_component(
    {"Savings": "#9467bd", "Wallets": "#8c564b", "Money": "#17becf", "Loans": "#e377c2"}
)

# Wrap the instance in solara.Reactive to prevent render loops.
# SolaraViz expects Model | solara.Reactive[Model].
model = solara.Reactive(Charts())

page = SolaraViz(
    model,
    components=[SpaceGraph, WealthClassChart, MoneySupplyChart],
    model_params=model_params,
    name="Mesa Charts - Bank Reserves",
)
