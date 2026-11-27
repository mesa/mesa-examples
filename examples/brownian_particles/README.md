# Brownian Particles

A simple model of particles diffusing through a 2D continuous space.

## What it shows

Each particle moves randomly each step (Brownian/random walk motion) and softly
repels nearby particles to avoid clustering. The colour of each particle reflects
how many neighbours it currently has — blue/purple means isolated, yellow/red
means densely packed.

This is a minimal example of **continuous space** in Mesa. There is no grid;
agents can be anywhere in a bounded region and interact based on Euclidean distance.

## How to run

```bash
cd examples/brownian_particles
solara run app.py
```

## Parameters

| Parameter | What it does |
|---|---|
| Number of Particles | Total agents in the space |
| Diffusion Rate | Size of random jump each step |
| Neighbor Detection Radius | Distance within which particles sense each other |

## Files

- `brownian_particles/agents.py` — Particle agent (Brownian motion + soft repulsion)
- `brownian_particles/model.py` — BrownianModel, handles setup and scheduling
- `app.py` — Solara visualization with interactive sliders
