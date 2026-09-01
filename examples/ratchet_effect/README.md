---
title: Ratchet Effect — Remote Work
authors:
  - abhinavk0220
domain:
  - labor-economics
  - behavioral
  - social-dynamics
complexity: intermediate
mesa_version_min: "3.0"
status: incubator
owner: abhinavk0220
llm_required: false
entry_point: app.py
---

## Abstract

This model demonstrates the [ratchet effect](https://en.wikipedia.org/wiki/Ratchet_effect) in labor markets: workers can shift toward remote work quickly, but the transition is very difficult to reverse once it has happened. The asymmetry emerges from two reinforcing mechanisms — structural (adaptation is faster than de-adaptation) and lock-in (the longer a worker is remote, the harder returning becomes). An optional external shock simulates a pandemic-like event, demonstrating path dependency: the post-shock equilibrium is permanently different from the pre-shock state.

Proposed by [@EwoutH](https://github.com/projectmesa/mesa-examples/issues/249).

## Background

The ratchet effect describes systems that move easily in one direction but resist moving in the opposite direction. Classic examples include wage rigidity, gentrification, and technology adoption. Remote work became a canonical case after 2020: surveys consistently show that once workers adapt to remote arrangements (home office investment, residential relocation, new social networks), employer attempts to mandate a return face disproportionate resistance.

This model abstracts the mechanism to its essentials to make the dynamics visible and interactive.

## Model Description

### Agents

**WorkerAgent** — placed on an `OrthogonalMooreGrid`, each worker has:
- `work_mode`: `"office"` or `"remote"`
- `lock_in` (0–1): accumulated investment in their current arrangement — represents home office setup, habits, and relocation combined into a single state variable
- `remote_preference` (−1 to 1): personal disposition, drawn from a Gaussian distribution with a slight positive bias

### Rules

**Going remote (easy direction):**
- Probability driven by: social contagion from neighbors + personal preference + employer openness + external shock
- `lock_in` increases by `adaptation_rate` each step remote (fast accumulation)

**Returning to office (hard direction — the ratchet):**
- Base probability = `institutional_pressure × return_rate`
- Multiplied by `(1 − lock_in)` — **this is the ratchet**: the probability of returning collapses as lock-in approaches 1.0
- Even after the shock ends, workers with high lock-in resist returning regardless of employer pressure
- `lock_in` decays only partially (−0.04 per return) — the investment is not fully reversible

### Space

15×15 `OrthogonalMooreGrid` (torus), one worker per cell. Neighbors influence each other's work mode decisions via social contagion.

### Parameters

| Parameter | Default | Description |
|---|---|---|
| `n_workers` | 100 | Number of worker agents |
| `initial_remote_fraction` | 0.05 | % starting remote |
| `adaptation_rate` | 0.08 | Lock-in gain per step remote |
| `return_rate` | 0.18 | Structural asymmetry factor for return |
| `social_influence` | 0.4 | Weight of neighbor work modes |
| `employer_remote_openness` | 0.3 | How remote-permissive the employer is |
| `shock_step` | 30 | Step at which shock hits (0 = no shock) |
| `shock_duration` | 8 | How many steps the shock lasts |

## How to Run

```bash
cd examples/ratchet_effect
pip install -r requirements.txt
solara run app.py
```

## Results & Discussion

**Without shock:** The system converges to a moderate remote equilibrium driven by preference heterogeneity and social influence. Workers with high remote preference convert first and pull neighbors via social contagion.

**With shock (default: step 30, duration 8):** Remote adoption spikes to near 100% during the shock period. After the shock ends, institutional pressure attempts to bring workers back — but average lock-in is now high, so `(1 − lock_in)` is small, and the ratchet holds. The system settles at a permanently higher remote equilibrium than it started from.

**Key observation:** Set `adaptation_rate = return_rate` and `lock_in` to not accumulate (set it to 0) — the ratchet disappears and the system is symmetric. This counterfactual makes the mechanism explicit.

**Visualization guide:**
- Grid: green squares = remote workers (darker/larger = higher lock-in), blue squares = office workers
- Top chart: Remote Workers % (green) and Return Resistance × 100 (red dashed); orange shading = shock period
- Bottom chart: Avg Lock-in over time — watch it ratchet upward and never fully recover

## References

- Lant Pritchett, ["The Ratchet Effect in Political Dynamics"](https://en.wikipedia.org/wiki/Ratchet_effect)
- EwoutH, [Mesa example model idea: Demonstrating the Ratchet Effect](https://github.com/projectmesa/mesa-examples/issues/249)
- Barrero, Bloom & Davis (2021), "Why Working From Home Will Stick", NBER Working Paper 28731
