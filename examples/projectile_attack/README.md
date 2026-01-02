# Projectile Attack GAME

## 1. Overview
- A simple 2D projectile game built with Mesa for the simulation core and tkinter for the GUI.
- Control a stationary tank on the left, fire shells with adjustable angle, power, wind, and wall settings to hit the target.
- Includes wind-drifted clouds, optional moving targets, wall wind-blocking logic, and explosion visuals.

## 2. Rule
- Only one shell can exist at a time; press Fire to launch when no shell is active.
- Shell motion follows gravity, wind acceleration, and a speed cap; walls block collision and can optionally block wind.
  - Wind blocking: when enabled, any cell at the wall column and the cells on the wind-upwind side within the wall height (ground y=1 up to `wall_height`, inclusive) ignore wind. If wind < 0, cells left of the wall are shielded; if wind > 0, cells right of the wall are shielded.
- Hitting the ground, leaving the grid, or striking the wall removes the shell; hitting the target ends the round and shows an explosion before auto-reset.
- If target movement is enabled, it oscillates vertically within bounds.

## 3. Installation
Prerequisites: Python 3.11+.
- Clone the repo, then install dependencies defined in `pyproject.toml`.
- With uv (recommended): `pip install uv` then `uv sync`.
- With pip: `pip install -e .` (installs `mesa` and typing stubs from `pyproject.toml`).

## 4. Project Structure
```
WEEK4_Projectile_Attack/
├─ README.md
├─ pyproject.toml
├─ uv.lock
├─ agents.py
├─ model.py
├─ run.py
└─ tank_game_vis.png
```
- `agents.py`: defines Tank, Shell, Target, and Cloud behaviors (physics, movement, collisions).
- `model.py`: builds the Mesa model, grid, scheduler, wall logic, explosions, and firing mechanics.
- `run.py`: tkinter UI for controls, rendering the grid, handling simulation loop, and user interactions.

## 5. Running the GAME
- From the project root: `python run.py`
- Adjust sliders (angle, power, wind, wall position/height), toggle wind blocking and target movement, then press Fire. Use Reset to restart with defaults.

## 6. Game interface
![Tank Game UI](tank_game_vis.png)

