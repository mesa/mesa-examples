# Surrogate Modeling with Scikit-learn and Mesa

This example demonstrates how to integrate Mesa with machine learning libraries like **Scikit-learn** to create a "surrogate model". It showcases a high-performance workflow for parameter exploration without the computational overhead of running thousands of full simulations.

## Summary

Agent-Based Models (ABMs) can be computationally expensive when exploring high-dimensional parameter spaces. This example illustrates a three-step surrogate modeling pipeline:

1. **Efficient Sampling**: Using **Latin Hypercube Sampling (LHS)** via `scipy.stats.qmc` to select a sparse but representative set of points across the parameter space.
2. **Simulation**: Running the Mesa model (WealthModel) at these sampled points to gather training data.
3. **Emulation**: Training a **Random Forest Regressor** on the simulation outcomes to create a surrogate that can predict model results (e.g., Gini coefficient) for any new parameter set nearly instantly.

This approach is particularly beneficial for calibration, sensitivity analysis, and optimization in complex models where running every possible configuration is infeasible.

## Installation

This example requires the `latest` version of Mesa and additional machine learning dependencies:

```bash
pip install mesa scikit-learn

```

## How to Run

To run the surrogate modeling workflow (sampling, training, and prediction), execute the analysis script from the root of the `mesa-examples` directory:

```bash
python -m examples.surrogate_modeling.analysis

```

## Files

* `model.py`: Contains the `WealthModel` and `WealthAgent` implementations, refactored for Mesa 4.0 "Lean Core" compatibility.
* `analysis.py`: Contains the LHS sampling logic, the manual training loop, and the Scikit-learn regressor integration.

## Model Details

### Logic

The example uses a refactored **Boltzmann Wealth Model**. Agents start with a fixed amount of wealth and exchange it randomly during interactions. The model calculates the **Gini coefficient** at the end of each run as the target metric for the surrogate model.

### Mesa 4.0 Integration

* **RNG Initialization**: Uses the `rng` parameter in `Model.__init__` to ensure future-proof compatibility and reproducibility.
* **Spatial Management**: Utilizes the `OrthogonalMooreGrid` and `CellAgent` pattern where agents are placed by sampling from `all_cells.cells`.
* **Agent Activation**: Uses `self.agents.shuffle_do("step")` for efficient agent execution.

## Further Reading

* **Latin Hypercube Sampling**: A statistical method for generating a near-random sample of parameter values from a multidimensional distribution.
* **Surrogate Modeling**: Also known as metamodeling or emulation, this is a technique used when an outcome of interest cannot be easily directly measured, so a model of the outcome is used instead.
* **Scikit-learn Random Forest**: [Random Forest Regressor Documentation](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html)