"""Interactive dashboard for the search and rescue model.

Run with::

    solara run app.py

Responders are coloured by the crew commanding them, so you can watch a medic
change colour as it is seconded to another crew and change back when it is
released. Victims are grey until discovered, then amber, or red if critical.
"""

import solara
from matplotlib.figure import Figure
from mesa.visualization import SolaraViz, SpaceRenderer
from mesa.visualization.components import AgentPortrayalStyle
from mesa.visualization.utils import update_counter
from sar import MEMBER, Crew, SARScenario, SearchAndRescueModel, Victim

CREW_COLOURS = [
    "#1f77b4",
    "#2ca02c",
    "#9467bd",
    "#8c564b",
    "#17becf",
    "#7f7f7f",
    "#bcbd22",
    "#e377c2",
    "#3b7a57",
    "#1b6ca8",
]


def _commanding_crew(agent):
    """Return the crew currently commanding a responder, if any."""
    for crew in agent.model.meta_agents.groups_of(agent):
        if isinstance(crew, Crew) and agent in crew.responders():
            return crew
    return None


def agent_portrayal(agent):
    """Colour victims by urgency and responders by commanding crew.

    Every style sets the same fields. Mesa's matplotlib backend collects each
    portrayal field into one array and masks it against all agents, so setting
    an optional field (``edgecolors``, ``linewidths``) on only some agents
    produces a ragged array and an IndexError at draw time.
    """
    if isinstance(agent, Victim):
        if not agent.discovered:
            colour, marker, size, zorder = "#c8c8c8", "x", 28, 1
        elif agent.needs_medic:
            colour, marker, size, zorder = "#d62728", "X", 80, 3
        else:
            colour, marker, size, zorder = "#ff9d3c", "X", 70, 3
        edge, width = "none", 0.0
    else:
        crew = _commanding_crew(agent)
        colour = CREW_COLOURS[crew.unique_id % len(CREW_COLOURS)] if crew else "#b0b0b0"
        if agent.is_medic:
            marker, size, zorder = "P", 95, 4
            edge, width = "black", 1.2
        else:
            marker, size, zorder = "o", 40, 2
            edge, width = "none", 0.0

    return AgentPortrayalStyle(
        color=colour,
        marker=marker,
        size=size,
        zorder=zorder,
        edgecolors=edge,
        linewidths=width,
    )


@solara.component
def ResponsePlot(model):
    """Cumulative rescued versus lost over time."""
    update_counter.get()
    figure = Figure(figsize=(5, 3))
    axis = figure.subplots()

    # Before the first step the recorder holds no rows, so the frame comes
    # back with no columns at all.
    frames = model.data_recorder.get_table_dataframe("response")
    if "rescued" in frames.columns:
        axis.plot(frames["time"], frames["rescued"], label="rescued", color="#2ca02c")
        axis.plot(frames["time"], frames["lost"], label="lost", color="#d62728")
        axis.legend(loc="upper left")
    else:
        axis.set_title("press play to start the response")

    axis.set_xlabel("time")
    axis.set_ylabel("victims")
    axis.grid(alpha=0.3)
    figure.tight_layout()
    return solara.FigureMatplotlib(figure)


@solara.component
def CommandStructure(model):
    """Live view of the command hierarchy and the borrowed medics."""
    update_counter.get()
    membership = model.meta_agents

    lines = [
        (
            f"**Span of control:** {model.span_of_control} "
            f"units reporting to incident command"
        ),
        (
            f"**Crews:** {model.n_crews} &nbsp;&nbsp; "
            f"**Task forces:** {model.n_task_forces}"
        ),
        (
            f"**Medics on loan right now:** {model.borrowed_medics} &nbsp;&nbsp; "
            f"**Total handoffs:** {model.medic_handoffs}"
        ),
    ]

    seconded = []
    for agent, group, relation in sorted(
        membership.backend.as_triplets(), key=lambda t: str(t[0])
    ):
        if relation != "attached":
            continue
        medic = next((a for a in model.agents if a.unique_id == agent), None)
        if medic is None:
            continue
        home = next(
            (
                str(g.unique_id)
                for g in membership.groups_of(medic, relation=MEMBER)
                if isinstance(g, Crew)
            ),
            "?",
        )
        seconded.append(f"- medic {agent}: home crew {home} → working crew {group}")

    if seconded:
        lines.append("**Currently seconded:**")
        lines.extend(seconded)

    return solara.Markdown("\n\n".join(lines))


model_params = {
    "rng": {"type": "InputText", "value": 42, "label": "Random seed"},
    "n_responders": {
        "type": "SliderInt",
        "value": 40,
        "min": 10,
        "max": 80,
        "step": 5,
        "label": "Responders",
    },
    "crew_size": {
        "type": "SliderInt",
        "value": 4,
        "min": 2,
        "max": 8,
        "step": 1,
        "label": "Crew size",
    },
    "medic_fraction": {
        "type": "SliderFloat",
        "value": 0.12,
        "min": 0.05,
        "max": 0.4,
        "step": 0.01,
        "label": "Fraction of responders who are medics",
    },
    "victim_interval": {
        "type": "SliderFloat",
        "value": 2.0,
        "min": 0.5,
        "max": 6.0,
        "step": 0.5,
        "label": "Time between new victims",
    },
    "pooled_specialists": {
        "type": "Checkbox",
        "value": True,
        "label": "Pool medics (crews may borrow)",
    },
}

model = SearchAndRescueModel(scenario=SARScenario(rng=42))

renderer = (
    SpaceRenderer(model, backend="matplotlib").setup_agents(agent_portrayal).render()
)

page = SolaraViz(
    model,
    renderer,
    components=[ResponsePlot, CommandStructure],
    model_params=model_params,
    name="Search and Rescue: overlapping command structure",
)
page  # noqa: B018
