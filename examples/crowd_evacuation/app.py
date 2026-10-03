"""Crowd Evacuation visualization using SolaraViz.

Displays the room layout with exits, person agents colored by speed,
and real-time charts tracking evacuation progress.
"""

import matplotlib.pyplot as plt
import numpy as np
import solara
from crowd_evacuation.agents import Person
from crowd_evacuation.model import EvacuationModel
from matplotlib.figure import Figure
from mesa.visualization import SolaraViz, make_plot_component

model_params = {
    "num_people": {
        "type": "SliderInt",
        "value": 80,
        "label": "Number of People:",
        "min": 10,
        "max": 200,
        "step": 10,
    },
    "width": {
        "type": "SliderInt",
        "value": 30,
        "label": "Room Width (m):",
        "min": 10,
        "max": 50,
        "step": 5,
    },
    "height": {
        "type": "SliderInt",
        "value": 20,
        "label": "Room Height (m):",
        "min": 10,
        "max": 50,
        "step": 5,
    },
    "num_exits": {
        "type": "SliderInt",
        "value": 2,
        "label": "Number of Exits:",
        "min": 1,
        "max": 4,
        "step": 1,
    },
    "exit_width": {
        "type": "SliderFloat",
        "value": 1.5,
        "label": "Exit Width (m):",
        "min": 0.5,
        "max": 3.0,
        "step": 0.5,
    },
    "desired_speed": {
        "type": "SliderFloat",
        "value": 1.3,
        "label": "Desired Speed (m/s):",
        "min": 0.5,
        "max": 3.0,
        "step": 0.1,
    },
}


@solara.component
def RoomDrawer(model):
    """Draw the evacuation room with exits and agents."""
    fig = Figure(figsize=(10, 7), dpi=100)
    ax = fig.subplots()

    width = model.width
    height = model.height

    # Draw room boundary
    ax.set_xlim(-1, width + 1)
    ax.set_ylim(-1, height + 1)
    ax.set_aspect("equal")

    # Draw walls (thick lines)
    wall_color = "#2c3e50"
    wall_lw = 3
    ax.plot([0, width], [0, 0], color=wall_color, linewidth=wall_lw)  # Bottom
    ax.plot([0, width], [height, height], color=wall_color, linewidth=wall_lw)  # Top
    ax.plot([0, 0], [0, height], color=wall_color, linewidth=wall_lw)  # Left
    ax.plot([width, width], [0, height], color=wall_color, linewidth=wall_lw)  # Right

    # Draw exits (green gaps in walls)
    for exit_pos, exit_w in model.exits:
        ex, ey = exit_pos
        ax.plot(
            ex,
            ey,
            marker="s",
            markersize=max(8, exit_w * 6),
            color="#27ae60",
            zorder=5,
            markeredgecolor="#1e8449",
            markeredgewidth=2,
        )
        ax.annotate(
            "EXIT",
            (ex, ey),
            fontsize=7,
            ha="center",
            va="center",
            fontweight="bold",
            color="white",
            zorder=6,
        )

    # Draw agents
    active_agents = [a for a in model.agents if isinstance(a, Person) and not a.escaped]

    if active_agents:
        positions = np.array([a.position for a in active_agents])
        speeds = np.array([np.linalg.norm(a.velocity) for a in active_agents])

        # Color by speed: slow=blue, fast=red
        max_speed = model_params["desired_speed"]["max"]
        norm_speeds = np.clip(speeds / max_speed, 0, 1)

        colors = plt.cm.RdYlBu_r(norm_speeds)  # Red=fast, Blue=slow

        ax.scatter(
            positions[:, 0],
            positions[:, 1],
            c=colors,
            s=25,
            alpha=0.85,
            edgecolors="#333",
            linewidths=0.5,
            zorder=10,
        )

    # Add info text
    remaining = model.num_people - model.agents_escaped
    ax.set_title(
        f"Crowd Evacuation — Step {int(model.time)} | "
        f"Remaining: {remaining} | Escaped: {model.agents_escaped}",
        fontsize=12,
        fontweight="bold",
    )
    ax.set_xlabel("x (meters)")
    ax.set_ylabel("y (meters)")

    # Color bar for speed
    sm = plt.cm.ScalarMappable(
        cmap=plt.cm.RdYlBu_r,
        norm=plt.Normalize(0, max_speed),
    )
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label("Speed (m/s)", fontsize=9)

    fig.tight_layout()

    return solara.FigureMatplotlib(fig)


def make_evacuation_curve(model):
    """Create the evacuation progress chart."""
    fig = Figure(figsize=(8, 4), dpi=100)
    ax = fig.subplots()

    data = model.datacollector.get_model_vars_dataframe()

    if len(data) > 0:
        ax.fill_between(
            data.index,
            data["Agents Remaining"],
            alpha=0.3,
            color="#e74c3c",
        )
        ax.plot(
            data.index,
            data["Agents Remaining"],
            color="#e74c3c",
            linewidth=2,
            label="Remaining",
        )
        ax.plot(
            data.index,
            data["Agents Escaped"],
            color="#27ae60",
            linewidth=2,
            label="Escaped",
        )

    ax.set_title("Evacuation Progress", fontweight="bold")
    ax.set_xlabel("Simulation Step")
    ax.set_ylabel("Number of Agents")
    ax.legend(loc="center right")
    ax.set_ylim(0, model.num_people + 5)

    fig.tight_layout()

    return solara.FigureMatplotlib(fig)


# Create initial model
model1 = EvacuationModel()

# Assemble the visualization
page = SolaraViz(
    model1,
    components=[
        RoomDrawer,
        make_evacuation_curve,
        make_plot_component("Average Speed"),
    ],
    model_params=model_params,
    name="Crowd Evacuation — Social Force Model",
    play_interval=100,
)

page  # noqa
