# Ant Colony — Task System Proof of Concept

A Mesa model demonstrating a proposed `Task` system ([discussion #2526](https://github.com/mesa/mesa/discussions/2526)).

## The problem this solves

Mesa agents have no concept of **duration**. Every action in `step()` is instantaneous — you cannot model an agent that is *busy*, that can be interrupted mid-task, or that earns partial rewards for incomplete work.

This example implements a minimal `Task` system that solves all four gaps identified in #2526.

## What it demonstrates

| Concept | How it appears in this model |
|---|---|
| Task duration | Digging takes 5 steps, transport 3, rest 2 |
| Priority queue | Urgent pheromone signal (priority 100) bumps ongoing dig (priority 10) |
| Interruptible tasks | Cave-in event interrupts any interruptible task in signal range |
| Resumable tasks | Interrupted dig resumes from progress; transport must restart |
| Partial rewards | 3/5 steps done → 60% reward (linear) |
| Threshold rewards | Transport only rewards on full completion |

## Running

```bash
pip install mesa solara
solara run app.py
```

## File structure

```
task_system_ant_colony/
├── tasks.py     # Task, TaskQueue, reward functions — reusable, model-agnostic
├── model.py     # AntColonyModel + AntAgent
├── app.py       # SolaraViz visualization
└── README.md
```

## Key design decisions

**`tasks.py` is model-agnostic.** Zero dependency on ant logic. Any Mesa agent can adopt it by calling `self.task_queue.step()` in its own `step()`.

**Duration is in simulation steps (int).** Keeps the API simple for most modellers. Float-time integration with `DiscreteEventScheduler` is a natural next step.

**Reward functions are pluggable callables** (`Callable[[float], float]`). Pass `linear_reward`, `threshold_reward`, `exponential_reward`, or any lambda — making the system RL-compatible later.

## Connection to GSoC 2026 Behavioral Framework

The `Task` system is the *execution layer* the Behavioral Framework is missing. Needs-based agents, BDI agents, and RL agents all need to act over time — not just decide instantly. `TaskQueue` bridges "agent decides" → "agent does it across multiple steps."

## Related

- [#2526 Tasks](https://github.com/mesa/mesa/discussions/2526) — origin of this concept (EwoutH)
- [#2538 Behavioral Framework](https://github.com/mesa/mesa/discussions/2538)
