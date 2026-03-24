# SIR Epidemic Model

## Abstract

This model simulates the spread of an infectious disease through a population using the classic Susceptible-Infected-Recovered (SIR) compartmental framework. Agents move randomly on a 2D grid, and infected agents can transmit the disease to susceptible neighbors with a configurable probability. After a set recovery period, infected agents become recovered and immune. The model demonstrates how epidemic dynamics emerge from simple local interaction rules.

## Background

The SIR model is one of the foundational frameworks in mathematical epidemiology, originally formulated by Kermack and McKendrick (1927). It divides a population into three compartments:

- **Susceptible (S):** Individuals who can contract the disease.
- **Infected (I):** Individuals who have the disease and can spread it.
- **Recovered (R):** Individuals who have recovered and are immune.

While the original SIR model uses differential equations to describe population-level dynamics, agent-based implementations allow exploration of spatial effects, stochastic variation, and heterogeneous contact patterns that differential equation models cannot capture.

## Model Description

### Agents

Each agent (`Person`) is a `CellAgent` on an `OrthogonalMooreGrid`. Agents have:
- A `state` attribute: "Susceptible", "Infected", or "Recovered"
- An `infection_timer` tracking how long they have been infected
- A `recovery_time` threshold for transitioning to "Recovered"

### Rules

At each step, every agent:
1. **Moves** to a random neighboring cell (Moore neighborhood).
2. **Spreads infection** (if infected): Each susceptible agent in the new cell's neighborhood is infected with probability `infection_rate`.
3. **Recovers** (if infected): After `recovery_time` steps, transitions to "Recovered".

### Space

A toroidal `OrthogonalMooreGrid` of configurable width and height. Multiple agents can occupy the same cell.

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `num_agents` | 100 | Total number of agents |
| `width` | 20 | Grid width |
| `height` | 20 | Grid height |
| `infection_rate` | 0.3 | Probability of transmission per contact |
| `recovery_time` | 10 | Steps until recovery |
| `initial_infected` | 3 | Number of initially infected agents |

## How to Run

### Install dependencies

```bash
pip install -U "mesa[rec]"
```

### Run the visualization

```bash
solara run app.py
```

### Run headless (no visualization)

```bash
python model.py
```

## Results and Discussion

With default parameters (100 agents, 30% infection rate, recovery time of 10 steps), the epidemic typically follows an S-shaped curve:

1. **Early phase (steps 1-10):** Slow spread as few agents are infected.
2. **Exponential growth (steps 10-25):** Rapid increase in infections as the disease spreads through the susceptible population.
3. **Peak and decline (steps 25-40):** Infections peak and decline as the susceptible pool is depleted.
4. **Equilibrium (steps 40+):** Nearly all agents have recovered; the epidemic ends.

The spatial nature of the model means that local clusters of infection can form and spread outward, creating wave-like patterns visible in the grid visualization.

## References

- Kermack, W. O., & McKendrick, A. G. (1927). A contribution to the mathematical theory of epidemics. *Proceedings of the Royal Society of London. Series A*, 115(772), 700-721.
- Wilensky, U. (1998). NetLogo Virus model. Center for Connected Learning and Computer-Based Modeling, Northwestern University.
