import numpy as np

from examples.forest_fire.forest_fire.model import ForestFire

m = ForestFire(width=100, height=100, density=0.65)
steps = 0
while m.running and steps < 1000:
    m.step()
    steps += 1
print(f"Model stopped after {steps} steps. Fire count: {np.sum(m.fire_state == 1)}")
