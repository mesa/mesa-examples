"""Solara visualization for the Dormant Alliances model.

Run:
    solara run app.py
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import networkx as nx
import solara
from matplotlib.figure import Figure

from mesa.visualization import SolaraViz
from mesa.visualization.utils import update_counter

from .model import DormantAlliancesModel
from .agents import Alliance, CountryAgent


# ---------------------------------------------------------------------------
# Solara components
# ---------------------------------------------------------------------------

# Colour coding: active alliance = blue, dormant = orange, unaffiliated = grey
_STATE_COLOUR = {
    "ACTIVE":  "#3B82F6",   # blue-500
    "DORMANT": "#F97316",   # orange-500
    None:      "#9CA3AF",   # grey-400  (unaffiliated)
}


@solara.component
def plot_alliance_network(model):
    """Draw the country-alliance network.

    Countries are nodes; an edge connects a country to its alliance.
    Node size reflects country power.  Alliance nodes are coloured by state.
    """
    update_counter.get()

    g = nx.Graph()

    countries = list(model.agents_by_type.get(CountryAgent, []))
    alliances  = list(model.agents_by_type.get(Alliance, []))

    # Add country nodes
    for c in countries:
        g.add_node(f"C{c.unique_id}", kind="country", power=c.power)

    # Add alliance nodes + edges
    for a in alliances:
        label = f"A{a.unique_id}\n{a.state.name[:3]}"
        g.add_node(label, kind="alliance", state=a.state.name)
        for member in a.agents:
            g.add_edge(f"C{member.unique_id}", label)

    pos = nx.spring_layout(g, seed=0)

    country_nodes  = [n for n, d in g.nodes(data=True) if d.get("kind") == "country"]
    alliance_nodes = [n for n, d in g.nodes(data=True) if d.get("kind") == "alliance"]

    country_sizes  = [g.nodes[n]["power"] * 3 for n in country_nodes]
    alliance_colours = [
        _STATE_COLOUR.get(g.nodes[n].get("state"), "#9CA3AF")
        for n in alliance_nodes
    ]

    fig = Figure(figsize=(7, 5))
    ax = fig.subplots()
    ax.set_title(
        f"Step {model.time}  |  "
        f"Countries: {len(countries)}  "
        f"Active alliances: {sum(1 for a in alliances if a.is_active)}  "
        f"Dormant: {sum(1 for a in alliances if a.is_dormant)}",
        fontsize=9,
    )

    nx.draw_networkx_nodes(g, pos, nodelist=country_nodes,
                           node_size=country_sizes, node_color="#6EE7B7", ax=ax)
    nx.draw_networkx_nodes(g, pos, nodelist=alliance_nodes,
                           node_size=600, node_color=alliance_colours,
                           node_shape="s", ax=ax)
    nx.draw_networkx_labels(g, pos, ax=ax, font_size=6)
    nx.draw_networkx_edges(g, pos, ax=ax, alpha=0.4)

    ax.axis("off")
    solara.FigureMatplotlib(fig)


@solara.component
def plot_timeseries(model):
    """Line chart: active vs dormant alliances and mean country power over time."""
    update_counter.get()

    df = model.datacollector.get_model_vars_dataframe()
    if df.empty:
        return

    fig = Figure(figsize=(7, 3))
    ax1, ax2 = fig.subplots(1, 2)

    ax1.plot(df.index, df["Active Alliances"],  label="Active",  color="#3B82F6")
    ax1.plot(df.index, df["Dormant Alliances"], label="Dormant", color="#F97316")
    ax1.set_title("Alliance States")
    ax1.set_xlabel("Step")
    ax1.set_ylabel("Count")
    ax1.legend(fontsize=7)

    ax2.plot(df.index, df["Mean Country Power"], color="#10B981")
    ax2.set_title("Mean Country Power")
    ax2.set_xlabel("Step")
    ax2.set_ylabel("Power")

    fig.tight_layout()
    solara.FigureMatplotlib(fig)


# ---------------------------------------------------------------------------
# Model parameters exposed in the Solara UI
# ---------------------------------------------------------------------------

model_params = {
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "n_countries": {
        "type": "SliderInt",
        "value": 20,
        "label": "Number of Countries",
        "min": 5,
        "max": 60,
        "step": 5,
    },
    "alliance_threshold": {
        "type": "SliderFloat",
        "value": 40.0,
        "label": "Alliance Formation Threshold",
        "min": 10.0,
        "max": 150.0,
        "step": 5.0,
    },
    "reactivation_interval": {
        "type": "SliderInt",
        "value": 5,
        "label": "Reactivation Check Interval",
        "min": 1,
        "max": 20,
        "step": 1,
    },
}

model = DormantAlliancesModel()

page = SolaraViz(
    model,
    components=[plot_alliance_network, plot_timeseries],
    model_params=model_params,
    name="Dormant Alliances — MetaAgent Lifecycle Demo",
)
page  # noqa

