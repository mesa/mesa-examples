# ML Optimization Demo

This is a simple demo showing how machine learning can find good model parameters automatically.

## What's the idea?

Finding good parameters for agent-based models takes forever. This project uses Gaussian Process regression (a type of machine learning) to:
- Try random parameters first to get a sense of what works
- Learn which parameters are correlated with good results
- Make smart guesses about which parameters to try next
- Eventually find better parameters than just random guessing

## How it works

Run the optimization in 2 phases:
1. Phase 1: Try 10 random parameter combinations
2. Phase 2: Use GP regression to make 20 smarter guesses based on what we learned in Phase 1

The results show ML finds around 14% better parameters on average compared to random search.

## What you can do with it

Run a single optimization:
```python
from examples.ml_optimization_demo import run_optimization
result = run_optimization()
```

Or run it multiple times to see if it's consistent:
```python
from examples.ml_optimization_demo import run_statistical_validation
stats = run_statistical_validation(num_runs=15)
print(f"Average improvement: {stats['mean_improvement']:.2f}%")
```

Or do both at once:
```python
from examples.ml_optimization_demo import run_full_analysis
run_full_analysis(num_runs=15)
```

## The parameters we're tuning

- num_agents: how many agents in the simulation (10 to 60)
- ratio: how much agents prefer their own type (0.3 to 0.8)
- exploration_bias: affects how agents explore (0.0 to 1.0)

## Why this approach works

- RBF kernel: simpler and more stable than other options
- Normalization: makes different parameters have similar scales so the model learns better
- Upper Confidence Bound: helps balance trying proven good parameters vs trying new ones
- Noise: adds realism so we're not overfitting to perfect data

## Quick start

```bash
pip install -r examples/ml_optimization_demo/requirements.txt
python -c "from examples.ml_optimization_demo import run_optimization; run_optimization()"
```

## Files

- model.py: the main optimization code
- agents.py: the agent class
- __init__.py: imports
- requirements.txt: dependencies
