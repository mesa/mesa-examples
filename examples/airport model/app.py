import solara
from mesa.visualization import SolaraViz, make_plot_component

from model import AirportModel


def runway_status_component(model):
    with solara.Column():
        solara.Markdown("## Runway Status")
        for runway in model.runways:
            aircraft = runway.current_aircraft
            solara.Markdown(
                f"""
**{runway.runway_id}**  
- Mode: {runway.mode}
- Operation: {runway.operation or "idle"}
- Occupied: {"yes" if aircraft else "no"}
- Aircraft: {getattr(aircraft, "flight_id", "-")}
- Remaining time: {runway.remaining_service_time}
"""
            )


def live_metrics_component(model):
    total_waiting = len(model.holding_queue) + len(model.takeoff_queue)

    with solara.Columns([1, 1, 1]):
        with solara.Card("Queues"):
            solara.Markdown(
                f"""
**Holding:** {len(model.holding_queue)}  
**Takeoff:** {len(model.takeoff_queue)}  
**Total waiting:** {total_waiting}
"""
            )

        with solara.Card("Outcomes"):
            solara.Markdown(
                f"""
**Landed:** {model.landed_count}  
**Departed:** {model.departed_count}  
**Diverted:** {model.diverted_count}  
**Cancelled:** {model.cancelled_count}
"""
            )

        with solara.Card("Time"):
            solara.Markdown(
                f"""
**Tick:** {model.tick_count}  
**Sim time:** {model.sim_time} min
"""
            )


model = AirportModel(
    num_runways=2,
    inbound_rate=12,
    outbound_rate=12,
    tick_size=1,
    landing_duration=4,
    takeoff_duration=3,
    emergency_fuel_threshold=25,
    minimum_fuel_threshold=10,
    max_takeoff_wait=40,
)

page = SolaraViz(
    model,
    components=[
        live_metrics_component,
        runway_status_component,
        make_plot_component(["holding_queue_size", "takeoff_queue_size"]),
        make_plot_component(["landed", "departed", "diverted", "cancelled"]),
        make_plot_component(["avg_wait_time"]),
    ],
    name="Airport Simulation",
)