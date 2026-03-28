# Information Cascades & Trading Behavior Model

This example implements a hybrid model of **Information Cascades and Trading Behavior** using **Mesa** and **Solara**.

The model studies how individual opinions evolve through repeated pairwise interactions (based on bounded confidence) and how investor overconfidence leads to excessive trading and wealth destruction.

---

## Model Description

Each investor agent holds a continuous opinion value in the range **(-1, 1)**, an overconfidence level between **(1.0, 5.0)**, and an initial wealth of **1000.0**.
At each time step:

1. A random pair of agents is selected.
2. If the difference between their opinions is less than a confidence threshold **ε (epsilon)**, they interact.
3. During an interaction, both agents adjust their opinions toward each other by a fraction **μ (mu)**, adjusted by their stubbornness (overconfidence).
4. Agents then execute trades with a probability based on their confidence level. Each trade deducts a fixed transaction cost from their wealth.

Depending on parameter values, the model can exhibit:
- Herd formation (Consensus)
- Echo chambers (Polarization and Fragmentation)
- Systematic wealth depletion due to overtrading

---

## Parameters

| Parameter               | Description |
|-------------------------|------------|
| `n`                     | Number of investors in the market |
| `epsilon (ε)`           | Confidence threshold controlling whether agents interact |
| `mu (μ)`                | Convergence rate controlling how strongly opinions are updated |
| `transaction_cost`      | The fee deducted from an agent's wealth per executed trade |

---

## Collected Metrics

The model tracks the following quantities over time:

- **Variance** – dispersion of opinions in the population
- **Avg Wealth** – the average remaining capital across all agents

These metrics are visualized alongside individual opinion trajectories and wealth distribution.

---

## Visualization

This example includes a Solara-based interactive visualization that shows:

- Opinion trajectories of all agents (Herd Formation)
- A scatter plot validating that "Trading is Hazardous to Your Wealth" (Confidence vs. Wealth)
- Opinion Variance over time
- Average Wealth over time
- Real-time trading performance stats

The market parameters can be adjusted in real-time using the sliders.

---

## Installation

To install the dependencies, use `pip` to install the requirements:

```bash
    $ pip install -r requirements.txt
```

From this directory, run:
```bash
    $ solara run app.py
```

Then open your browser to local host http://localhost:8765/ and press Reset, then Step or Play.

## Files
- model.py: Defines the TradingDWModel, including market parameters, agent interactions, and data collection.
- agents.py: Defines the InvestorAgent class, the logic for updating agent opinions, and the trading execution mechanism.
- app.py: Contains the code for the interactive Solara visualization, including opinion trajectories, scatter plots, and custom performance metrics.


## References
- Barber, B. M., & Odean, T. (2000).
Trading is hazardous to your wealth: The common stock investment performance of individual investors.
The Journal of Finance, 55(2), 773-806.

- Banerjee, A. V. (1992).
A simple model of herd behavior.
The Quarterly Journal of Economics, 107(3), 797-817.
