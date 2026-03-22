# Needs-Based Wolf-Sheep

An extension of the classic Wolf-Sheep predation model that
explores **needs-based behavioral architecture** from Mesa
discussion [#2538](https://github.com/projectmesa/mesa/discussions/2538).

## What's different from standard Wolf-Sheep

In the standard model, every agent checks all conditions every
tick — energy thresholds, reproduction probability, nearby prey —
regardless of whether anything changed.

This model restructures that logic using **explicit internal drive
states** that degrade over time and determine action priority:

| Drive | Agent | Behaviour when urgent |
|-------|-------|-----------------------|
| `hunger` | Wolf, Sheep | Prioritise eating |
| `fear` | Sheep | Suppress eating, flee |

## Key behavioral difference
```python
# Standard Wolf-Sheep — all checked every tick
if self.energy > 20:
    if random() < p_reproduce:
        self.reproduce()

# Needs-based — action only fires when drive is urgent
if self.hunger > 0.6:     # only when actually hungry
    self._eat_nearest_prey()
```

## Connection to Mesa discussions

- [#2538 Behavioral Framework](https://github.com/projectmesa/mesa/discussions/2538)
  — State system, drive-based decision making
- [#2526 Tasks](https://github.com/projectmesa/mesa/discussions/2526)
  — Desire-based modelling, internal states

## Running the model
```bash
pip install mesa
python model.py
```