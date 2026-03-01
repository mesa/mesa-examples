# Hexagonal Ant Foraging

A simple agent-based model simulating ant foraging behavior on a hexagonal grid. Agents (ants) leave the nest to find food, following pheromone trails. When they find food, they return to the nest, depositing a different pheromone to recruit other ants.

## Features

-   **HexGrid**: Demonstrates `mesa.discrete_space.HexGrid` (toroidal).
-   **PropertyLayer**: Uses `mesa.discrete_space.PropertyLayer` for efficient pheromone and resource management (NumPy-backed).
-   **Solara Visualization**: Interactive visualization using `SolaraViz` and `make_space_component`.

## Installation

To install the dependencies for this example, run:

```bash
pip install mesa[rec]
```

## How to Run

To run the visualization:

```bash
solara run examples/hex_ant/app.py
```
