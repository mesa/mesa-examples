import solara
from matplotlib.figure import Figure
from mesa.visualization import Slider, SolaraViz, make_plot_component
from mesa.visualization.utils import update_counter

try:
    from .model import BusLine, BusLineScenario
except ImportError:
    from model import BusLine, BusLineScenario

model_params = {
    "rng": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "n_stops": Slider("Number of stops", 6, 2, 12, 1),
    "stop_spacing": Slider("Stop spacing (m)", 300, 100, 1000, 50),
    "capacity": Slider("Bus capacity", 30, 5, 80, 5),
    "dwell_time": Slider("Dwell time (s)", 15, 0, 60, 1),
    "boarding_time": Slider("Boarding time per passenger (s)", 3.0, 0.5, 10.0, 0.5),
    "arrival_rate": Slider("Arrivals per stop per second", 0.02, 0.0, 0.1, 0.005),
    "cruise_speed": Slider("Cruise speed (m/s)", 12, 5, 25, 1),
}


@solara.component
def plot_route(model):
    """Draw the stops in a row, with the waiting queue at each and the bus."""
    update_counter.get()
    bus = model.bus
    n = model.n_stops
    waiting = [len(model.waiting_at(stop)) for stop in range(n)]

    fig = Figure(figsize=(7, 2.6))
    ax = fig.subplots()
    ax.bar(range(n), waiting, color="tab:orange", width=0.5, label="Waiting")

    # The bus runs a loop, so its position is shown within the current lap.
    lap_position = (bus.position / bus.stop_spacing) % n
    marker = "s" if bus.doors_open_at is not None else ">"
    ax.plot(lap_position, -0.6, marker=marker, markersize=12, color="tab:blue")

    ax.set_xticks(range(n), [f"Stop {i}" for i in range(n)])
    ax.set_xlim(-0.6, n - 0.4)
    ax.set_ylim(-1.2, max(*waiting, 5) + 1)
    ax.set_ylabel("Waiting")
    doors = "doors open" if bus.doors_open_at is not None else "driving"
    ax.set_title(
        f"t={model.time:.0f}s   |   {bus.speed:.1f} m/s   |   {doors}   |   "
        f"on board {len(bus.riders)}/{bus.capacity}"
    )
    fig.tight_layout()
    solara.FigureMatplotlib(fig)


SpeedPlot = make_plot_component({"Speed": "tab:blue"})
CrowdingPlot = make_plot_component({"Waiting": "tab:orange", "On board": "tab:green"})
ServicePlot = make_plot_component({"Left behind": "tab:red", "Delivered": "tab:purple"})


model = BusLine(scenario=BusLineScenario())

page = SolaraViz(
    model,
    components=[plot_route, SpeedPlot, CrowdingPlot, ServicePlot],
    model_params=model_params,
    name="Bus Line Model",
)
page  # noqa
