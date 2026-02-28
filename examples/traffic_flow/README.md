# Traffic Flow (Mesa ABM)

A minimal traffic flow agent-based model built with the Mesa framework (tested with Mesa `3.3.1`).

The model uses a discrete grid world with cars that move only from left to right. When a car reaches the right edge, it wraps back to the left using a torus grid.

## What this model does

- The world is a `width x height` `MultiGrid` with `torus=True`.
- Cars are placed randomly at initialization (one car per cell).
- Each simulation step (a “tick”), every car attempts to move one cell to the right:
  - If the cell is empty, it moves.
  - If the cell is occupied, it waits.

## Core rules / logic

- **Movement check**: a car checks the cell at `(x+1, y)`.
- **Wrap-around**: since the grid is a torus, moving past the right edge returns to the left edge.
- **No overtaking**: cars do not change lanes or move diagonally (future feature).

## Project structure

- `traffic_flow/agent.py`
  - `CarAgent`: defines movement behavior (`move`) and agent step (`step`).
- `traffic_flow/model.py`
  - `TraficFlow`: creates the grid, places cars, and advances the model.
- `run.py`
  - CLI runner that prints the grid as ASCII each tick.
- `app.py`
  - Solara UI entrypoint using `mesa.visualization.SolaraViz`.

## Requirements

- Python 3.8+
- Mesa 3.x (this was built with Mesa `3.3.1`)
- Solara (only required for UI)

Install (example):

```bash
pip install "mesa[rec]" solara
```

## How to run (CLI)

From the `examples/traffic_flow` directory:

```bash
python run.py
```

### Output format

- `C` = a car occupies the cell
- `.` = empty cell

Each printed block corresponds to one simulation step (a “tick”).

## How to run (Solara UI)

From the `examples/traffic_flow` directory:

```bash
solara run app.py
```

Open the URL shown in your terminal.

### Using the sliders

The parameter widgets typically apply to the next model instance. After changing sliders, use the UI control to reset/restart the model so it rebuilds with the new parameters.

## Model parameters

- `width` (int): grid width
- `height` (int): grid height
- `n_cars` (int): number of cars placed initially
- `seed` (int/str): random seed passed to the Mesa model

### Practical limits

- `n_cars` should be less than or equal to `width * height`.
  - If `n_cars` is close to `width * height`, initialization can slow down because the model searches repeatedly for empty cells.

