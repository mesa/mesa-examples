# Needs-Based Wolf-Sheep Predation

## Summary

An extension of Mesa's core [Wolf-Sheep Predation](https://github.com/projectmesa/mesa/tree/main/mesa/examples/advanced/wolf_sheep) model that replaces hardcoded behavioral rules with a **needs-based behavioral architecture**. Animals have continuous internal states — hunger, fear, and fatigue — that evolve each simulation step. Behavior is driven by whichever need is most pressing at any moment, creating more realistic and emergent dynamics.

This model was built as part of evaluating how well Mesa supports established behavioral theories, following the approach described in Mesa's [Behavioral Framework project](https://github.com/mesa/mesa/wiki/GSoC-2026-Project-Ideas#behavioral-framework) and the discussions on [Continuous States (#2529)](https://github.com/projectmesa/mesa/discussions/2529), [Tasks (#2526)](https://github.com/projectmesa/mesa/discussions/2526), and [Behavioral Framework (#2538)](https://github.com/projectmesa/mesa/discussions/2538).

## How It Works

### Internal States (Needs)

Each animal tracks three continuous internal states (floats from 0.0 to 1.0):

| Need | What drives it | How it's satisfied |
|------|---------------|--------------------|
| **Hunger** | Increases as energy drops below maximum | Eating (sheep eat grass, wolves eat sheep) |
| **Fear** | Spikes when predators are nearby | Moving away from threats |
| **Fatigue** | Increases with movement | Resting in place |

### Decision Mechanism

Each step, the agent selects the action corresponding to its highest need:
- **Fear > all** → Flee (move away from threats)
- **Hunger > all** → Eat (seek and consume food)
- **Fatigue > all** → Rest (stay in place, recover)
- **All needs low** → Explore (move randomly)

A small base "exploration drive" (0.15) ensures agents move even when all needs are satisfied.

### Key Differences from Core Wolf-Sheep

| Aspect | Core Wolf-Sheep | Needs-Based |
|--------|----------------|-------------|
| Decision logic | Fixed: move → eat → reproduce | Dynamic: highest need wins |
| Movement cost | Always 1 energy | Varies: flee costs 1.5, rest costs 0.3 |
| Fear response | Sheep avoid wolf cells (fixed) | Fear is a continuous state that competes with hunger/fatigue |
| Wolf behavior | Always hunt if sheep nearby | Hungry wolves hunt; tired wolves rest; desperate wolves panic |
| Emergent patterns | Predator-prey cycles | Predator-prey cycles + fatigue-driven rest patterns + fear waves |

## How to Run

Install Mesa with recommended dependencies:

```
pip install "mesa[rec]"
```

Then run:

```
solara run app.py
```

In the browser visualization:
- **Red squares** = Wolves (darker red = hungrier)
- **Blue circles** = Sheep (darker blue = more afraid)
- **Green/brown squares** = Grass (green = fully grown)

## Documented Friction Points

Building this model surfaced several friction points relevant to Mesa's behavioral framework discussion:

1. **No continuous state abstraction** — Internal needs are plain floats updated manually each step. There's no way to declare "hunger increases at rate 0.05/tick" or trigger events at threshold crossings (e.g., "when hunger > 0.8, interrupt current activity"). Discussion #2529 proposes exactly this.

2. **No spatial query helpers** — "Count wolves within radius 2" requires iterating over neighborhood cells and filtering by type. A common operation in behavioral models that could benefit from a utility like `cell.neighborhood.count_type(Wolf, radius=2)`.

3. **Sequential activation bias** — `shuffle_do` activates sheep before wolves (or vice versa), giving one species a slight first-mover advantage. For needs-based models where timing matters (a sheep that flees *before* a wolf hunts vs *after*), this ordering affects dynamics. Simultaneous activation would be more natural.

4. **DataCollector with dynamic populations** — Collecting "average hunger of living wolves" requires a custom lambda that handles the empty-set case. Common enough in behavioral models to warrant a built-in helper.

## Files

- `agents.py` — NeedsBasedAnimal base class, NeedsSheep, NeedsWolf, NeedsGrass
- `model.py` — NeedsWolfSheep model with data collection
- `app.py` — Solara-based interactive visualization

## Further Reading

- Mesa core Wolf-Sheep: [mesa/examples/advanced/wolf_sheep](https://github.com/projectmesa/mesa/tree/main/mesa/examples/advanced/wolf_sheep)
- Continuous States discussion: [#2529](https://github.com/projectmesa/mesa/discussions/2529)
- Tasks discussion: [#2526](https://github.com/projectmesa/mesa/discussions/2526)
- Behavioral Framework discussion: [#2538](https://github.com/projectmesa/mesa/discussions/2538)
- Wilensky, U. (1997). NetLogo Wolf Sheep Predation model.
