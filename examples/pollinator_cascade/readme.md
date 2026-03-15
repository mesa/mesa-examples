## Pollinator-Plant Cascade Extinction Model

A Mesa agent-based model simulating cascade extinctions in a bipartite
pollinator-plant mutualistic network. Models how losing pollinators causes
delayed plant collapse: a real ecological phenomenon linked to colony
collapse and habitat loss.

## Overview

Pollinators (bees, butterflies, etc.) and plants are connected in a bipartite
network where edges only exist between the two types, never within. Each
agent has continuous energy/health attributes that respond to the state
of their network neighbors. When pollinators die, plants lose support and
eventually collapse, potentially triggering further pollinator loss.

The key emergent behavior is the lag effect that shows plants survive for several
steps after their pollinators die, then collapse rapidly. This mirrors real
ecosystem dynamics where resilience masks underlying fragility.

## Installation
```bash
git clone <your-repo-url>
cd pollinator_cascade
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Model

**Static analysis (3-panel chart):**
```bash
python run.py
```

**Interactive dashboard:**
```bash
solara run app.py
```

## Parameters

- **n_pollinators** (default: 20) — number of pollinator agents in the simulation
- **n_plants** (default: 30) — number of plant agents in the simulation
- **connectivity** (default: 0.35) — probability that any pollinator-plant pair is connected. Lower values produce sparser, more fragile networks
- **extinction_schedule** (default: [30, 60, 90]) — steps at which one random pollinator is forcibly removed, simulating external shocks like pesticide use or habitat loss
- **rng** (default: 42) — random seed for reproducibility

## Model Details

**Agents:**
- `Pollinator` — gains energy from alive connected plants, loses energy
  each step. Specialists (high specialization) pay higher energy costs,
  making them more vulnerable to cascade failures.
- `Plant` — health tracks the fraction of alive pollinator partners.
  Resilient plants decline slower and survive longer into the cascade, 
  staggering deaths across many steps.

**Network:**
Built using `networkx.bipartite.random_graph` and wrapped in Mesa's
`Network` discrete space. Lower connectivity produces sparser, more
fragile networks where single pollinator losses have larger impacts.

**Cascade mechanism:**
At each step agents check their network neighbors via `cell.connections`.
Dead agents are removed from `model.agents` after each step. Cascade depth
is tracked as a running counter on the model since dead agents are no
longer queryable.

## Output

**run.py produces 3 panels:**
- Survival rates of both species over time
- Cumulative plant deaths (cascade depth)
- Survival gap showing the lag between pollinator and plant loss

**app.py produces an interactive dashboard with:**
- Page 1: Live survival rate and cascade depth charts
- Page 2: Real-time energy and health distribution histograms

## Project Structure
```
pollinator_cascade/
├── agents.py       # Pollinator and Plant agent classes
├── model.py        # Model, network setup, data collection
├── run.py          # Run model and generate static charts
├── app.py          # Interactive Solara dashboard
├── readme.md       # This file
├── requirements.txt
├── data/
└── images/         # Output charts saved here
```

## References

- Bascompte, J. & Jordano, P. (2007). Plant-animal mutualistic networks.
  *Annual Review of Ecology, Evolution, and Systematics.*
- Memmott, J. et al. (2004). Tolerance of pollination networks to species
  extinctions. *Proceedings of the Royal Society B.*
```
