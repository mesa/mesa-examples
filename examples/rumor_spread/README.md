# Rumor Spread Model

## Summary
This is a small agent-based model built with Mesa to simulate rumor propagation on a 2D grid.

Each agent occupies one cell in the grid. A small number of agents initially know the rumor. At each step, informed agents may spread the rumor to their neighbors. Each agent also has an individual resistance value, which reduces the probability of becoming informed.

The model includes:
- a spatial visualization of rumor spread
- a time-series plot showing how many agents are informed over time
- interactive controls for the number of initial spreaders and infection strength

## Purpose
I built this model as part of my Mesa GSoC 2026 preparation to gain hands-on experience with:
- Mesa model structure
- cell-based agents and grid spaces
- Solara-based visualization
- parameterized simulation experiments

## Model behavior
- Agents are placed on a toroidal 20x20 grid
- A configurable number of agents start informed
- Informed agents try to spread the rumor to neighboring agents
- Each agent has a resistance value between 0 and 1
- Higher resistance reduces the chance of becoming informed
- Informed agents can forget the rumor with a certain probability (recovery)

## Behavior

The model exhibits three regimes:

- Extinction: rumor dies out
- Equilibrium: stable fluctuations
- Saturation: near-total spread

These regimes depend on infection_strength and recovery_rate.

## Parameters
- **Initial Spreaders**: number of agents that start with the rumor
- **Infection Strength**: base strength of rumor transmission
- **Recovery Rate**: probability of forgetting the rumor each step

## What I learned
While building this model, I learned:
- the difference between generic Mesa agents and `CellAgent`
- how to use `OrthogonalMooreGrid` and assign agents to cells
- how to collect aggregate metrics with `DataCollector`
- how to render a model using `SolaraViz` and `SpaceRenderer`
- Introduced a recovery mechanism to prevent full saturation and allow more realistic steady-state behavior.
- how small design choices strongly affect emergent dynamics

## How to run
From this directory:

```bash
solara run app.py
```

## Notes

This model is intentionally simple. Its goal is not to be a realistic rumor diffusion simulator, but to serve as a compact, reproducible Mesa example for experimentation and learning.

## Quick observations
- Lower infection strength slows down diffusion and makes the growth curve less abrupt.
- A higher number of initial spreaders accelerates saturation.
- Even in a simple model, agent-level heterogeneity (resistance) changes the global diffusion pattern.
- With recovery, the model reaches a steady state instead of full infection, showing realistic epidemic-like dynamics.