# Wolf-Sheep Predation Model

## Summary

A classic predator-prey model demonstrating Lotka-Volterra dynamics using Mesa's
cell-based discrete space.

Wolves and sheep move around a grid. Sheep eat grass to gain energy; wolves eat
sheep. Both species reproduce probabilistically and die when their energy runs out.
When grass regrowth is enabled, eaten grass patches regenerate after a fixed number
of steps.

The model reproduces the characteristic population oscillations described by
Lotka-Volterra equations — sheep boom when wolves are scarce, wolves boom when
sheep are abundant, leading to cyclic dynamics.

Based on the NetLogo model:
> Wilensky, U. (1997). NetLogo Wolf Sheep Predation model.
> http://ccl.northwestern.edu/netlogo/models/WolfSheepPredation.
> Center for Connected Learning and Computer-Based Modeling,
> Northwestern University, Evanston, IL.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `initial_sheep` | 100 | Starting sheep population |
| `initial_wolves` | 25 | Starting wolf population |
| `sheep_reproduce` | 0.04 | Probability a sheep reproduces each step |
| `wolf_reproduce` | 0.05 | Probability a wolf reproduces each step |
| `wolf_gain_from_food` | 20 | Energy gained by a wolf from eating a sheep |
| `sheep_gain_from_food` | 4 | Energy gained by a sheep from eating grass |
| `grass` | True | Whether grass regrowth is enabled |
| `grass_regrowth_time` | 30 | Steps for an eaten grass patch to regrow |

## Installation

```bash
pip install mesa[rec]
```

## How to Run

```bash
solara run app.py
```

Then open your browser to [http://localhost:8765/](http://localhost:8765/).

## Mesa Concepts Demonstrated

- `OrthogonalMooreGrid` from `mesa.discrete_space`
- `CellAgent` and `FixedAgent` for multi-type agents on a cell space
- `schedule_event` for deferred actions (grass regrowth)
- `agents_by_type` for per-class stepping order
- `DataCollector` with multiple population reporters
- `SolaraViz` with `make_space_component` and `make_plot_component`
