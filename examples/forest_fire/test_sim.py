import numpy as np
from forest_fire.model import ForestFire

m = ForestFire(width=100, height=100, density=0.65)
print(f"Initial ON_FIRE: {np.sum(m.fire_state == 1)}")
print(f"Initial FINE: {np.sum(m.fire_state == 0)}")
print(f"Initial EMPTY: {np.sum(m.fire_state == -1)}")

for i in range(5):
    m.step()
    print(f"Step {i + 1} ON_FIRE: {np.sum(m.fire_state == 1)}")
    if not m.running:
        print("Model stopped!")
        break
