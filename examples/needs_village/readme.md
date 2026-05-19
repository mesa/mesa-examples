# Needs-Based Village

A population of villagers on a Moore grid each manage four competing
homeostatic needs: **HUNGER**, **REST**, **SOCIAL**, and **SAFETY**.
At every step each villager acts on whichever need is most urgent,
moving toward the relevant resource or partner and satisfying the need on arrival.

This model demonstrates a *needs-based (homeostatic)* decision-making
architecture — a third paradigm alongside reactive agents and BDI deliberation.

## Key Concepts

### How decisions are made

Each villager's step follows a fixed cycle:

```
perceive()          scan for nearby ThreatAgents → update SAFETY
_decay_needs()      autonomously advance HUNGER, REST, SOCIAL
most_urgent_need()  select the highest-urgency need
act_on_need()       move toward the relevant target; satisfy on arrival
```

Unlike a BDI agent, villagers have no explicit goals or plans.
They are *pushed* by internal drives that grow continuously and can
only be suppressed, never permanently satisfied.  Crucially, priorities
can flip mid-movement — a SAFETY spike while en route to food forces
the villager to flee instead, abandoning the half-completed journey.

### The four needs

| Need | Decay | Satisfied by | Notes |
|------|-------|-------------|-------|
| HUNGER | 0.045/step | Eating at a `FoodSource` | Resource-competitive: finite supply |
| REST | 0.030/step | Standing near a `HomePatch` | Location-based |
| SOCIAL | 0.020/step | Being adjacent to another villager | **Mutual**: both partners benefit |
| SAFETY | 0 (perception-driven) | Distance from `ThreatAgent` | Spikes rapidly; dissipates when threat leaves |

### Agents

| Class | Type | Behaviour |
|-------|------|-----------|
| `VillagerAgent` | `NeedsAgent` | Manages four needs; greedy movement |
| `ThreatAgent` | `CellAgent` | Random walk; spikes SAFETY of nearby villagers |
| `FoodSource` | `CellAgent` | Stationary; stores up to 6 food units, regenerates 1/step |
| `HomePatch` | `CellAgent` | Stationary rest site |

## Running

```bash
pip install -r requirements.txt
solara run app.py
```

Then open [http://127.0.0.1:8765](http://127.0.0.1:8765).

The interactive sliders let you vary villager count, resource density,
and threat count in real time.

### CLI batch run

```python
from needs_village import VillageModel

model = VillageModel(n_villagers=20, n_threats=2, rng=42)
for _ in range(200):
    model.step()

df = model.datacollector.get_model_vars_dataframe()
print(df[["MeanHunger", "MeanRest", "CriticalAgents", "TotalPreemptions"]].tail())
```

## What to observe

**Threat effect:** Set `Threats = 0` vs `Threats = 4` and observe how
SAFETY preemptions raise all other mean need levels — villagers cannot
attend to HUNGER, REST, or SOCIAL while fleeing.

**Food scarcity:** Reduce food patches to 2–3.  Mean HUNGER rises and
stays elevated; villagers compete for the same patches, and social
interaction drops as they spread out.

**Social clustering:** With plenty of food and no threats, SOCIAL becomes
the dominant active need late in the run.  Villagers form loose clusters
because mutual satisfaction means two agents next to each other both
improve simultaneously.

## Architectural note: NeedsAgent vs BDI

| Property | BDI | NeedsAgent |
|----------|-----|------------|
| Decision driver | Explicit goals (pull) | Internal drives (push) |
| Priority source | Deliberation over desires | Urgency ordering of floats |
| Plan horizon | Multi-step intention queue | Single next action |
| Interruption | Plan invalidation on world change | Continuous preemption on priority flip |
| Termination | Goal achieved | Need suppressed (never eliminated) |

The two architectures are complementary: needs can parametrise BDI
desires dynamically (e.g. HUNGER > 0.6 activates the FORAGE desire).

## Files

```
needs_village/
├── needs_village/
│   ├── __init__.py
│   ├── agents.py   — NeedSpec, NeedsAgent (abstract), all concrete agents
│   └── model.py    — VillageModel, DataCollector setup
├── app.py          — Solara visualisation (4 panels)
├── readme.md
└── requirements.txt
```
