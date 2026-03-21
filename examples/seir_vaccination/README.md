# SEIR Epidemic Model with Vaccination Policy

**Mesa Version:** >=3.0 | **Visualization:** SolaraViz

---

## Overview

This model simulates how a disease spreads through a population on a grid, and how a government responds when things get bad enough.

Each person on the grid goes through four states — Susceptible, Exposed, Infected, and Recovered. A government meta-agent watches the infection rate every step and kicks off vaccination campaigns once it crosses a threshold, directly moving some susceptible people to recovered.

The interesting part is watching the tension between how fast the disease spreads bottom-up and how quickly the government can slow it down top-down.

Based on the classic SEIR compartmental model: Kermack, W. O., & McKendrick, A. G. (1927). A contribution to the mathematical theory of epidemics. *Proceedings of the Royal Society of London*, 115(772), 700–721.

---

## How to Run
```bash
pip install mesa[rec]
python -m solara run app.py
```

---

## What the Colors Mean

| Color | State | What it means |
|---|---|---|
| 🔵 Blue | Susceptible | Healthy, can be infected |
| 🟠 Orange | Exposed | Infected but not contagious yet |
| 🔴 Red | Infected | Contagious, spreading to neighbors |
| 🟢 Green | Recovered | Immune, out of the chain |

---

## Parameters

| Parameter | Default | Description |
| `width` / `height` | 30 | Grid size |
| `initial_infected` | 5 | How many people start infected |
| `transmission_rate` | 0.3 | Chance of catching it from an infected neighbor |
| `incubation_period` | 3 | Days before Exposed becomes contagious |
| `infection_duration` | 7 | Days before recovery |
| `vaccination_threshold` | 0.1 | Infection rate that triggers a campaign |
| `vaccination_rate` | 0.05 | Fraction of susceptible people vaccinated per campaign |