# Continuous Space Predator-Prey Model

## Summary
This model simulates a predator-prey ecosystem in Mesa's experimental `ContinuousSpace`. It demonstrates realistic biological behaviors including lifespans, mating requirements, and energy-based reproduction.

This model has been updated to **Mesa 4.0 standards**, using the native `agents.shuffle_do()` activation and automatic agent ID management.

## Agents

### Prey
- **Movement:** Random motion through continuous space
- **Lifespan:** Maximum age of 40 steps (die of old age)
- **Mating:** Requires at least 1 mate nearby to reproduce
- **Carrying Capacity:** Will NOT reproduce if 6+ prey are nearby (simulates overcrowding/limited resources)
- **Reproduction:** Asexual cloning when conditions are favorable

### Predators
- **Movement:** Random motion with higher speed than prey
- **Lifespan:** Maximum age of 60 steps (die of old age)
- **Energy System:** Lose 1 energy per step, gain energy from eating prey
- **Starvation:** Die immediately if energy reaches 0
- **Hunting:** Hunt prey within radius of 4.0
- **Reproduction:** Only reproduce when energy > 30 (must be well-fed)

## Biological Features

This model implements realistic Lotka-Volterra population dynamics:

1. **Natural Death:** Both species die of old age, preventing immortality
2. **Mating Constraints:** Prey need mates nearby, preventing infinite cloning
3. **Overcrowding:** Prey reproduction limited by local population density
4. **Energy-Based Reproduction:** Predators only reproduce after successful hunting
5. **Starting Energy:** Predators spawn with random energy to survive initial hunting

## How to Run

### Interactive Visualization (SolaraViz)
To launch the interactive web dashboard with sliders and real-time visualization:

```bash
solara run app.py
```

This will open a web browser with:
- **Spatial Map:** Blue circles (Prey) and red triangles (Predators) moving in continuous space
- **Population Chart:** Real-time line graph showing prey and predator population cycles
- **Interactive Sliders:** Adjust initial populations and reproduction rates

### Headless Mode
To run a headless benchmark of the model for 50 steps:

```bash
python run.py
```

## Installation

Make sure you have Mesa installed:

```bash
pip install -r requirements.txt
```

For the interactive visualization, also ensure `solara` is installed:

```bash
pip install solara
```

## Model Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `width` | 100 | Width of the continuous space |
| `height` | 100 | Height of the continuous space |
| `initial_prey` | 100 | Starting prey population |
| `initial_predators` | 20 | Starting predator population |
| `prey_reproduce` | 0.04 | Probability of prey reproduction per step |
| `predator_reproduce` | 0.05 | Probability of predator reproduction per step |
| `predator_gain_from_food` | 20 | Energy gained by predator when eating prey |

## Expected Behavior

When running the simulation, you should observe **Lotka-Volterra population cycles**:

1. Prey population grows rapidly (blue line rises)
2. Predator population follows as food becomes abundant (red line rises)
3. Prey population crashes due to predation (blue line falls)
4. Predator population crashes due to starvation (red line falls)
5. Cycle repeats as prey recover

The population chart should show the classic "chasing waves" pattern where the red predator line follows the blue prey line with a time delay.

## Code Formatting

Mesa strictly enforces the PEP8 coding standard. Run this command in your terminal to automatically format your files:

```bash
ruff check . --fix
ruff format .
```

## Files

- `model.py` - Main model class with Mesa 4.0 native activation
- `agents.py` - Prey and Predator agent classes with biological behaviors
- `app.py` - SolaraViz interactive visualization
- `run.py` - Headless simulation runner
