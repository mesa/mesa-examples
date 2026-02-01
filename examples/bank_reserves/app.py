from bank_reserves.agents import Person
from bank_reserves.model import BankReservesModel
from mesa.visualization import (
    SolaraViz,
    make_plot_component,
    make_space_component,
)
from mesa.visualization.components import AgentPortrayalStyle
from mesa.visualization.user_param import (
    Slider,
)

# The colors here are taken from Matplotlib's tab10 palette
# Green
RICH_COLOR = "#2ca02c"
# Red
POOR_COLOR = "#d62728"
# Blue
MID_COLOR = "#1f77b4"


def person_portrayal(agent):
    if agent is None:
        return

    # update portrayal characteristics for each Person object
    if isinstance(agent, Person):
        color = MID_COLOR

        # set agent color based on savings and loans
        if agent.savings > agent.model.rich_threshold:
            color = RICH_COLOR
        if agent.savings < 10 and agent.loans < 10:
            color = MID_COLOR
        if agent.loans > 10:
            color = POOR_COLOR

        return AgentPortrayalStyle(
            marker="o",
            size=50,
            zorder=0,
            color=color,
        )


def post_process_space(ax):
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])


def post_process_lines(ax):
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.9))


# dictionary of user settable parameters - these map to the model __init__ parameters
model_params = {
    "init_people": Slider(
        "People",
        25,
        1,
        200,
        # description="Initial Number of People"
    ),
    "rich_threshold": Slider(
        "Rich Threshold",
        10,
        1,
        20,
        # description="Upper End of Random Initial Wallet Amount",
    ),
    "reserve_percent": Slider(
        "Reserves",
        50,
        1,
        100,
        # description="Percent of deposits the bank has to hold in reserve",
    ),
}

space_component = make_space_component(
    person_portrayal,
    draw_grid=False,
    post_process=post_process_space,
)
lineplot_component = make_plot_component(
    {"Rich": RICH_COLOR, "Poor": POOR_COLOR, "Middle Class": MID_COLOR},
    post_process=post_process_lines,
)
model = BankReservesModel(init_people=25, rich_threshold=10, reserve_percent=50)

page = SolaraViz(
    model,
    components=[space_component, lineplot_component],
    model_params=model_params,
    name="Bank Reserves Model",
)
page  # noqa
