# LLM Epidemic Model

## Summary

A classic SIR (Susceptible-Infected-Recovered) epidemic simulation where agents use **LLM Chain-of-Thought reasoning** to decide their behavior during an outbreak.

Unlike traditional SIR models with fixed stochastic transition probabilities, agents here _reason_ about their situation — weighing personal health risk, observed neighbor states, and community responsibility — before choosing an action:

- **isolate** — Stay home, reduce infection risk
- **move_freely** — Normal activity, higher transmission risk
- **seek_treatment** — If infected, accelerate recovery

This produces epidemic curves that reflect _reasoning-driven behavioral responses_ rather than purely stochastic transitions, demonstrating how LLM-powered agents can model nuanced human decision-making during crises.

## Visualization

| Color | State |
|-------|-------|
| 🔵 Blue | Susceptible |
| 🔴 Red | Infected |
| 🟢 Green | Recovered |

- **Circle (○)** — Agent moving freely
- **Square (□)** — Agent isolating

The SIR plot tracks population counts over time, showing how LLM-driven behavioral choices shape the epidemic curve.

## How to Run

```bash
pip install -r requirements.txt
solara run app.py
```

## Model Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `num_agents` | 20 | Total agents in simulation |
| `initial_infected` | 3 | Agents infected at start |
| `grid_size` | 10 | Size of the spatial grid |
| `llm_model` | gemini/gemini-2.0-flash | LLM backend for reasoning |

## Key Insight

The epidemic curve shape depends heavily on how agents reason. An LLM that emphasizes community responsibility will produce faster isolation responses and flatter curves, while one that emphasizes personal freedom produces sharper peaks — mirroring real-world behavioral heterogeneity during outbreaks.

## Reference

Kermack, W. O., & McKendrick, A. G. (1927). A contribution to the mathematical theory of epidemics. *Proceedings of the Royal Society of London. Series A*, 115(772), 700–721.
