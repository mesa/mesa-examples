import numpy as np
from smart_traffic_lights.model import TrafficModel

STEPS = 2000

width = 20
height = 20
num_cars_east = 8
num_cars_north = 8


def final_results_from_simulation(smart_lights: bool):
    model = TrafficModel(smart_lights=smart_lights)
    model.run_for(STEPS)
    df = model.datacollector.get_model_vars_dataframe()
    return df.iloc[-1]


def percent_reduction(before, after):
    return np.round((before - after) / before * 100, 2)


def improvement_report(statistic_name, val_before, val_after):
    improvement = percent_reduction(val_before, val_after)
    return f"""
    {"-" * 40}
    Results after {STEPS} steps:
    {statistic_name} (Static Lights): {val_before} steps
    {statistic_name} (Smart Lights) : {val_after} steps
    Performance Improvement: {improvement}% reduction
    {"-" * 40}"""


print("Running Static Traffic Lights Simulation...")
final_results_static = final_results_from_simulation(smart_lights=False)

print("Running Smart Traffic Lights Simulation...")
final_results_smart = final_results_from_simulation(smart_lights=True)

final_wait_static = final_results_static["Total_Red_Light_Wait_Time"]
final_wait_smart = final_results_smart["Total_Red_Light_Wait_Time"]
print(
    improvement_report("Total Red Light Wait Time", final_wait_static, final_wait_smart)
)

final_wait_static = final_results_static["Total_Wait_Time"]
final_wait_smart = final_results_smart["Total_Wait_Time"]
print(improvement_report("Total Wait Time", final_wait_static, final_wait_smart))
