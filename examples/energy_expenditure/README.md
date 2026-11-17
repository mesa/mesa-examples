# Energy Expenditure

This example explores a simple question:

> How do agents survive when every action costs energy?

Each agent has a limited internal energy that decreases over time.
They must balance between moving (which helps exploration but costs energy) and resting (which recovers energy slowly).

## Model Behavior

- Every step reduces energy
- Moving costs additional energy
- Resting allows partial recovery
- Agents are removed when their energy reaches zero

## What to Observe

When you run the model:

- Agents initially move actively across the grid
- Over time, movement slows as energy drops
- The population gradually decreases
- Some agents survive longer by conserving energy

This creates a simple but meaningful trade-off between activity and survival.

## Why this example

This model demonstrates **state-driven behavior**, where decisions are based on an agent's internal condition rather than randomness.

It serves as a minimal foundation for:

- resource-based simulations
- survival dynamics
- adaptive agent behavior

## Run the model

```bash
pip install -r requirements.txt
solara run app.py
```
