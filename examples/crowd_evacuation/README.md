# Crowd Evacuation — Social Force Model

## Summary

This model simulates how people evacuate a room. It's based on [Helbing & Molnár's Social Force Model](https://doi.org/10.1103/PhysRevE.51.4282) (1995) — the idea that pedestrian movement can be modeled as if people are pushed around by invisible forces:

1. **"I want to get out"** — each person is pulled toward the nearest exit
2. **"Don't crowd me"** — people push away from each other to avoid collisions
3. **"That's a wall"** — people push away from room boundaries

These three simple rules, when combined, produce realistic crowd behavior: bottlenecks form at exits, people slow down when it gets crowded, and wider exits actually help (as you'd expect).

This is the kind of simulation used in real building design and fire safety planning.

### Observed Behavior

When you run the model, you'll see:
- Agents start scattered randomly across the room
- They quickly orient toward the nearest exit and begin moving
- As agents converge on exits, they slow down due to social repulsion
- A natural bottleneck forms at each exit opening
- Agents closest to exits escape first; those farther away arrive in waves
- With default settings (80 people, 2 exits), full evacuation takes around 1000–2000 steps (~100–200 simulated seconds)

### What It Demonstrates

This is a **Continuous Space** example. It showcases:

- **`ContinuousSpace`** — a bounded 2D room (not a torus)
- **`ContinuousSpaceAgent`** — agents with smooth, real-valued positions
- **Vector arithmetic** — velocity-based movement using `self.position += velocity * dt`
- **`get_neighbors_in_radius()`** — finding nearby agents for social force computation
- **Dynamic agent state** — agents are marked `escaped` when they reach an exit
- **`DataCollector`** — tracking agents remaining, escaped count, and average speed
- **`SolaraViz`** — interactive visualization with parameter sliders

## How to Run

Make sure you have mesa installed:

```bash
pip install mesa[viz] numpy matplotlib
```

Interactive visualization:

```bash
solara run app.py
```

Headless (no GUI):

```python
from crowd_evacuation.model import EvacuationModel

model = EvacuationModel(num_people=20, num_exits=2)
model.run_for(500)
print(f"Escaped: {model.agents_escaped} / {model.num_people}")
print(f"Simulated time: {model.time * model.dt:.0f} seconds")
```

Expected output: all 20 agents escape within 500 steps.

## Parameters

| Parameter | Default | What it does |
|-----------|---------|-------------|
| `num_people` | 80 | How many people in the room |
| `width` | 30 | Room width in meters |
| `height` | 20 | Room height in meters |
| `num_exits` | 2 | Number of exit doors (1–4, placed on opposite walls) |
| `exit_width` | 1.5 | How wide each exit is (meters) |
| `desired_speed` | 1.3 | How fast people *want* to walk (m/s) |
| `max_speed` | 2.0 | Hard speed limit (m/s) |

## Files

- **`model.py`** — `EvacuationModel`: sets up the room, exits, and data collection
- **`agents.py`** — `Person`: the social force logic (desired + social + wall forces)
- **`app.py`** — SolaraViz visualization with room layout and evacuation progress chart

## Interesting Things to Try

- Set `num_exits` to 1 and watch the bottleneck form
- Crank up `num_people` to 200 and see how long evacuation takes
- Compare `desired_speed` = 1.0 vs 3.0 — does wanting to go faster actually help? (Spoiler: not always — this is the "faster-is-slower" effect from Helbing's paper)

## References

- Helbing, D., & Molnár, P. (1995). Social force model for pedestrian dynamics. *Physical Review E*, 51(5), 4282.
- Helbing, D., Farkas, I., & Vicsek, T. (2000). Simulating dynamical features of escape panic. *Nature*, 407(6803), 487–490.
