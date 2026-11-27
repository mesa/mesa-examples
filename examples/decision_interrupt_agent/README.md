# Decision Interrupt Agent Example

This example demonstrates **agent-level interruptions** in Mesa
using **event-based scheduling** instead of step-based counters.

## Motivation

Many Mesa models implement long-running actions (e.g. jail sentences,
cooldowns, delays) using counters inside `step()`. This example shows
how such behavior can be modeled more naturally using scheduled events.

## Key Concepts Demonstrated

- Agent actions with duration (jail sentence)
- Event-based interruption and resumption
- No polling or step counters
- Minimal logic inside `step()`

## Model Description

- Agents normally perform actions when FREE
- At scheduled times, one agent is arrested
- Arrested agents do nothing while IN_JAIL
- Release is handled automatically via a scheduled event

## Files

- `agents.py` – Agent logic with interruption and release
- `model.py` – Model-level scheduling of arrests
- `run.py` – Minimal script to run the model

## How to Run

python run.py
