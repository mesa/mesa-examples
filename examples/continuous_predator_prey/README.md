# Continuous Space Predator-Prey

## Summary
This model simulates a predator-prey ecosystem in Mesa's experimental `ContinuousSpace`. It was specifically built to serve as a performance benchmark for the dynamic adding and removing of `ContinuousSpaceAgent`s (via births, deaths, and starvation) during runtime.

## Agents
* **Prey:** Move randomly through the continuous space and reproduce with a set probability.
* **Predators:** Expend energy to move. They hunt nearby Prey within a specific radius, gaining energy when they eat. If their energy reaches 0, they die. If they reproduce, their energy is split with their offspring.

## How to Run
To run a headless benchmark of the model for 50 steps, navigate to this directory and run:

```bash
python run.py
```
## Step 2: Format Your Code
Mesa strictly enforces the PEP8 coding standard. If your code is messy, the automated GitHub Actions will reject your PR before a human even looks at it.

Run this command in your terminal (make sure you are inside the `continuous_predator_prey` folder) to automatically format your files:
```bash
ruff check . --fix
ruff format .
```