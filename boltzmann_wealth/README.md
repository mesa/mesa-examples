# Boltzmann Wealth Model

## Summary
A simple agent-based model demonstrating wealth distribution.
Each agent starts with 1 unit of wealth and randomly gives it
to another agent each step. Over time, wealth inequality emerges
even though everyone started equal.

## How to Run
Install dependencies:
```
pip install mesa seaborn matplotlib
```

Run the model:
```
python model.py
```

## What You Will See
A histogram showing wealth distribution after 30 steps.
Most agents end up with 0 wealth while a few become rich.

## Key Concepts
- **Agents**: Individual people with wealth
- **Exchange**: Random wealth transfer each step
- **Emergence**: Inequality appears from equal starting conditions