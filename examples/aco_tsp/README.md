---
title: Ant Colony Optimization - TSP
authors:
  - Crow-1701
domain:
  - optimization
  - combinatorics
complexity: intermediate
mesa_version_min: "4.0"
status: incubator
keywords: [ant colony, TSP, optimization, swarm intelligence]
---

## Abstract
An implementation of Ant Colony Optimization (ACO) solving the Travelling Salesman Problem (TSP). Artificial ants explore routes between cities, leaving pheromone trails that guide future ants toward shorter paths.

## Model Description
- **Agents:** Ant agents that traverse cities leaving pheromone trails
- **Rules:** Ants probabilistically choose next city based on pheromone strength and distance. Shorter routes accumulate stronger pheromones over time.
- **Space:** Network of cities loaded from berlin52.txt dataset
- **Parameters:** n_ants, evaporation_rate, alpha, beta

## How to Run
```bash
pip install -r requirements.txt
solara run app.py
```

## Results & Discussion
The colony progressively finds shorter routes across generations. Pheromone trails visualize the emergent collective intelligence of the swarm.

## References
- Dorigo & Gambardella (1997), Ant Colony System