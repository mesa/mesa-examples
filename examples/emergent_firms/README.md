# Emergent Firms — Endogenous Firm Formation (Axtell 1999)

## Summary

This model implements the endogenous firm formation framework described in The Emergence of Firms in a Population of Agents: Local Increasing Returns, Unstable Nash Equilibria, and Power Law Size Distributions (Axtell, 1999). It demonstrates how firms can emerge, grow, shrink, and dissolve purely from the decentralized decisions of boundedly-rational workers — without any top-down market mechanism or central planner.

Each worker is endowed with a Cobb-Douglas utility function over income and leisure, parameterized by an idiosyncratic preference θ. Every period a randomly activated worker evaluates three options:

1. **Stay** in their current firm
2. **Start** a new singleton firm
3. **Join** a friend's firm

The worker chooses whichever option maximizes their expected utility via a 101-point line search over effort levels. Firms are *meta-agents* whose output follows a super-linear production function O(E) = aE + bE^β, where E is total worker effort. Income is split equally among firm members, creating a public-goods tension: larger firms produce more per-capita output, but free-riding erodes individual incentives. The one optional change from the original model is agents can expand their network from 2 to n. (Although larger networks, will cause the model to slow significantly).

The resulting dynamics reproduce several empirical regularities observed in real economies, including right-skewed firm-size distributions, persistent firm entry and exit, and heterogeneous effort levels across workers.

**Of Note:** This model does not use the Solara visualization/interface module, instead is uses a custom javascript visualization/interface. See install and run instructions below.

## Installation

Install the dependencies with `pip`:

```bash
pip install mesa[rec] fastapi uvicorn
```

## How to Run

Launch the FastAPI visualization server:

```bash
uvicorn app:app --reload
```

Then open your browser to [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

Use the control panel to configure parameters, initialize the model, and step through the simulation. The dashboard displays real-time charts tracking firm counts, size distributions, effort, output, income, and utility — alongside an interactive firm Rank Clock visualization and a drill-down view for individual workers.

## Parameters

| Parameter | Default | Description |
|---|---|---|
| `num_agents` | 1000 | Number of workers in the economy |
| `a` | 1.0 | Linear coefficient in production function |
| `b` | 1.0 | Nonlinear coefficient in production function |
| `beta` | 2.0 | Returns-to-scale exponent (β > 1 → increasing returns) |
| `num_friends` | 2 | Size of each worker's static social network |
| `make_friends` | False | Whether workers befriend a coworker when joining a new firm |
| `max_friends` | 10 | Maximum friend network size when `make_friends` is enabled (retains highest-utility friends) |

## Files

* `emergent_firms/model.py` — Model class (`FirmModel`), scenario parameters (`FirmScenario`), model-level reporters, and data collection logic.
* `emergent_firms/agents.py` — `Worker` agent (utility optimization, firm evaluation, movement decisions) and `Firm` meta-agent (production, income allocation).
* `app.py` — FastAPI backend serving the interactive visualization, with REST endpoints for init, step, reset, and drill-down queries.
* `static/index.html` — Single-page dashboard UI.
* `static/index.css` — Dashboard styling.
* `static/app.js` — Client-side logic and Chart.js / D3 visualizations.

## Key Concepts

### Meta-Agents
Firms are managed through Mesa's `MetaAgents` membership system rather than maintaining their own member lists. This cleanly separates group identity from individual agent logic.

### Production & Free-Riding
With β > 1, the production function exhibits increasing returns to scale, making large firms collectively more productive. However, equal income sharing means individual workers can reduce effort without proportional income loss — the classic free-rider problem. The emergent equilibrium balances these forces.

## Further Reading

- Axtell, R. L. (2018). *The Complexity of Exchange.* Oxford University Press. (Chapter 3)
- Axtell, R. L. (1999). The Emergence of Firms in a Population of Agents. *Santa Fe Institute Working Paper 99-03-019*.
- Axtell, R. L. (2001). Zipf Distribution of U.S. Firm Sizes. *Science*, 293(5536), 1818–1820.
