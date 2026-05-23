# The Emperor's Dilemma Agent-Based Model

This is a Python implementation of the Agent-Based Model (ABM) described in:

[Centola, D., Willer, R., & Macy, M. (2005). The Emperor’s Dilemma: A Computational Model of Self‐Enforcing Norms1. American Journal of Sociology.](https://www.journals.uchicago.edu/doi/10.1086/427321)

The model simulates how unpopular norms can dominate a society even when the vast majority of individuals privately reject them. It demonstrates the "illusion of consensus" where agents, driven by a fear of appearing disloyal, not only comply with a rule they hate but also aggressively enforce it on their neighbors. This phenomenon creates a "trap" of False Enforcement, where the loudest defenders of a norm are often its secret opponents.

The model tracks three key metrics:

1. *Compliance:* The fraction of agents publicly obeying the norm.
2. *Enforcement:* The fraction of agents punishing deviants.
3. *False Enforcement:* The fraction of agents who privately hate the norm but enforce it anyway to signal sincerity.

## Installation

```bash
pip install mesa matplotlib solara
```

## How to Run

```bash
solara run app.py
```

## Extensions

This model has been extended with the following additions:

### Whistleblower Agents
A new `WhistleblowerAgent` subclass that is immune to social pressure
and always acts on private belief publicly. Use the **Fraction Whistleblowers**
slider to introduce them into the simulation.

### Belief Gap Metric
Tracks the average distance between private belief and public behavior
across all agents at each step. A value near 1.0 means the society is
wearing a collective mask. A value near 0.0 means everyone is acting
honestly.

### Norm Collapse Detection
The model records exactly which step compliance first drops below 50%,
turning a visual observation into a measurable data point accessible
via `model.collapse_step`.

### Key Finding
There is a sharp tipping point around 5-10% whistleblowers. Below this
threshold the norm holds completely. Above it the norm collapses rapidly.
This threshold behavior emerges from the local interaction rules rather
than being explicitly programmed.