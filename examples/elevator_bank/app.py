"""Solara app for the Elevator Bank model.

Run with ``solara run app.py`` from this directory.
"""

import solara
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from mesa.visualization import Slider, SolaraViz, make_plot_component
from mesa.visualization.utils import update_counter

try:
    from .model import ElevatorBank, ElevatorScenario
except ImportError:
    from model import ElevatorBank, ElevatorScenario

CAR_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]

model_params = {
    "rng": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "n_floors": Slider("Floors", 12, 2, 40, 1),
    "n_cars": Slider("Cars", 2, 1, 6, 1),
    "max_speed": Slider("Cruise speed (m/s)", 2.5, 0.5, 6.0, 0.5),
    "acceleration_rate": Slider("Acceleration (m/s^2)", 1.0, 0.25, 3.0, 0.25),
    "door_time": Slider("Door time (s)", 8, 0, 30, 1),
    "mean_call_gap": Slider("Mean time between calls (s)", 25, 5, 120, 5),
}


@solara.component
def shaft_view(model):
    """Draw the shafts, the floors with a waiting call, and every car."""
    update_counter.get()
    n_cars = len(model.cars)
    n_floors = model.n_floors

    fig = Figure(figsize=(1.6 + 1.1 * n_cars, 5.5))
    ax = fig.subplots()

    for k in range(n_floors):
        ax.axhline(k, color="#dddddd", linewidth=0.8, zorder=0)
    for floor in {call.floor for call in model.waiting}:
        ax.plot(-0.35, floor + 0.45, marker=">", color="#d62728", markersize=8)

    for i, car in enumerate(model.cars):
        color = CAR_COLORS[i % len(CAR_COLORS)]
        y = car.floor
        ax.add_patch(
            Rectangle(
                (i + 0.2, y),
                0.6,
                0.9,
                facecolor=color,
                alpha=0.95 if car.doors_open else 0.6,
                edgecolor="black",
            )
        )
        if car.doors_open:
            label = "doors"
        elif car.moving:
            label = f"{car.velocity:+.1f} m/s"
        else:
            label = "idle"
        ax.text(
            i + 0.5,
            y + 0.45,
            label,
            ha="center",
            va="center",
            fontsize=7,
            color="white",
        )

    ax.set_xlim(-0.6, n_cars)
    ax.set_ylim(-0.3, n_floors)
    ax.set_xticks([i + 0.5 for i in range(n_cars)])
    ax.set_xticklabels([f"Car {i}" for i in range(n_cars)])
    ax.set_yticks(range(n_floors))
    ax.set_ylabel("Floor")
    ax.set_title(
        f"t = {model.time:.0f} s   |   {len(model.waiting)} waiting   |   "
        f"{len(model.wait_times)} answered",
        fontsize=9,
    )
    fig.tight_layout()

    solara.FigureMatplotlib(fig)


WaitingPlot = make_plot_component({"Waiting calls": "#d62728"})
MeanWaitPlot = make_plot_component({"Mean wait (s)": "#1f77b4"})


model = ElevatorBank(scenario=ElevatorScenario())

page = SolaraViz(
    model,
    components=[shaft_view, WaitingPlot, MeanWaitPlot],
    model_params=model_params,
    name="Elevator Bank",
)
page  # noqa
