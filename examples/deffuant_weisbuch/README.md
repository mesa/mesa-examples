# Deffuant–Weisbuch Bounded Confidence Model

This example implements the **Deffuant–Weisbuch bounded confidence model** of opinion dynamics using **Mesa** and **Solara**.

The model studies how individual opinions evolve through repeated pairwise interactions when agents are only willing to interact with others whose opinions are sufficiently close to their own.

---

## Model Description

Each agent holds a continuous opinion value in the range **(-1, 1)**.
At each time step:

1. A random pair of agents is selected.
2. If the difference between their opinions is less than a confidence threshold **ε (epsilon)**, they interact.
3. During an interaction, both agents adjust their opinions toward each other by a fraction **μ (mu)**.

Depending on parameter values, the model can exhibit:
- Consensus
- Polarization
- Fragmentation into multiple opinion clusters

---

## Parameters

| Parameter | Description |
|---------|------------|
| `n` | Number of agents in the population |
| `epsilon (ε)` | Confidence threshold controlling whether agents interact |
| `mu (μ)` | Convergence rate controlling how strongly opinions are updated |
| `seed` | Random seed for reproducibility |

---

## Collected Metrics

The model tracks the following quantities over time:

- **Variance** – dispersion of opinions in the population
- **Acceptance rate** – fraction of attempted interactions that lead to opinion updates
- **Cluster count** – number of distinct opinion clusters (based on a distance threshold)

These metrics are visualized alongside individual opinion trajectories.

---

## Visualization

This example includes a Solara-based interactive visualization that shows:

- Opinion trajectories of all agents
- Variance over time
- Acceptance rate over time
- Number of opinion clusters

The model parameters can be adjusted in real-time using the sliders.

---

## Installation

To install the dependencies use `pip` to install `mesa[rec]`

```bash
    $ pip install mesa[rec]
```

## Running the Example

From this directory, run:

```bash
    $ solara run app.py
```

Then open your browser to local host [http://localhost:8765/](http://localhost:8765/) and press Reset, then Run.

## Files

* `model.py`: Defines the Deffuant–Weisbuch bounded confidence model, including model parameters, agent interactions, and data collection.
* `agents.py`: Defines the `OpinionAgent` class and the logic for updating agent opinions during interactions.
* `app.py`: Contains the code for the interactive Solara visualization, including opinion trajectories and summary metrics.


## References

This model is drawn from the bounded confidence opinion dynamics framework introduced by Deffuant et al. (2000).

- Deffuant, G., Neau, D., Amblard, F., & Weisbuch, G. (2000).
  *Mixing beliefs among interacting agents*.
  **Advances in Complex Systems**, 3(01n04), 87–98.
  https://doi.org/10.1142/S0219525900000078
