import numpy as np
from smart_traffic_lights.model import TrafficModel

STEPS = 2000

width = 20
height = 20
num_cars_east = 8
num_cars_north = 8


print("Running Static Traffic Lights Simulation...")
model_static = TrafficModel(smart_lights=False)
for _ in range(STEPS):
    model_static.step()

print("Running Smart Traffic Lights Simulation...")
model_smart = TrafficModel(smart_lights=True)
for _ in range(STEPS):
    model_smart.step()

# Retrieve data
static_df = model_static.datacollector.get_model_vars_dataframe()
smart_df = model_smart.datacollector.get_model_vars_dataframe()

# Calculate the percentage improvement
final_wait_static = static_df["Total_Red_Light_Wait_Time"].iloc[-1]
final_wait_smart = smart_df["Total_Red_Light_Wait_Time"].iloc[-1]

improvement = np.round(
    (final_wait_static - final_wait_smart) / final_wait_static * 100, 2
)

print("-" * 40)
print(f"Results after {STEPS} steps:")
print(f"Total Red Light Wait Time (Static Lights): {final_wait_static} steps")
print(f"Total Red Light Wait Time (Smart Lights) : {final_wait_smart} steps")
print(
    f"Performance Improvement        : {improvement}% reduction in red light wait time"
)
print("-" * 40)

final_wait_static = static_df["Total_Wait_Time"].iloc[-1]
final_wait_smart = smart_df["Total_Wait_Time"].iloc[-1]

improvement = np.round(
    (final_wait_static - final_wait_smart) / final_wait_static * 100, 2
)

print("-" * 40)
print(f"Total Wait Time (Static Lights): {final_wait_static} steps")
print(f"Total Wait Time (Smart Lights) : {final_wait_smart} steps")
print(f"Performance Improvement        : {improvement}% reduction in total wait time")
print("-" * 40)
