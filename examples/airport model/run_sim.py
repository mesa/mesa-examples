# run_sim.py
from model import AirportModel
from viz import show_all_plots

model = AirportModel(
    num_runways=2,
    inbound_rate=12,
    outbound_rate=12,
    tick_size=1,
    landing_duration=4,
    takeoff_duration=3,
    emergency_fuel_threshold=25,
    minimum_fuel_threshold=10,
    max_takeoff_wait=40
)

for _ in range(300):
    model.step()

show_all_plots(model)