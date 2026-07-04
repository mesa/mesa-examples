# Zero-Intelligence Double Auction

## Summary

A continuous double-auction market with zero-intelligence traders. Buyers and
sellers each receive a private value: buyers have a maximum willingness to pay,
and sellers have a minimum acceptable cost. Agents arrive asynchronously, submit
random bids or asks constrained by their private values, and trade whenever the
best bid crosses the best ask. The clearing price is the midpoint of the matched
bid and ask.

The model tracks transaction prices, cumulative volume, bid-ask spread, agent
wealth, inventory, and whether each trader has completed its single-unit trade.
It can be run interactively with Solara or as a scripted simulation that plots
supply, demand, transaction prices, volume, and spread.

The model demonstrates the following Mesa features:

- Agent object inheritance for buyer and seller trader types
- Event-based/asynchronous agent activation with scheduled arrivals
- DataCollector for model-level and agent-level results
- SolaraViz sliders for changing model parameters interactively
- A simple order book with price-time priority and trade matching

## Installation

Install the Mesa examples dependencies from the `mesa-examples` package. From
the `mesa-examples` directory, use:

```bash
pip install -e .
```

If you are running only this example manually, make sure the environment includes
Mesa, Solara, matplotlib, pandas, and pytest for tests.

## Interactive Model Run

To run the model interactively, use `solara run notebook/app.py` in this
directory:

```bash
solara run notebook/app.py
```

Then open your browser to the local Solara URL, select the model parameters,
press Reset, then Start.

## Scripted Run

To run a scripted simulation and generate a summary plot, run
`notebook/run_simulation.py` in this directory:

```bash
python notebook/run_simulation.py
```

The script prints recent model data, compares transaction prices with the
theoretical competitive equilibrium from the sampled private values, and saves a
figure to `notebook/simulation_results.png`.

## Tests

To run the tests for this example from the repository root:

```bash
python -m pytest mesa-examples/examples/zi_double_auction/tests
```

The tests check agent counts, initial inventories, event scheduling, time
advancement, volume limits, DataCollector output, no-loss trades, and removal of
completed traders from the order book.

## Files

- `model/model.py`: Defines `DoubleAuctionModel`, creates buyers and sellers,
  records data, and settles matched trades.
- `model/agents.py`: Defines the base `Trader` class and the `Buyer` and
  `Seller` subclasses.
- `model/order_book.py`: Defines orders, trades, bid/ask submission, price-time
  priority, spread calculation, and matching logic.
- `model/__init__.py`: Exports the public model, agent, order book, order, and
  trade classes.
- `notebook/app.py`: Launches the interactive Solara visualization.
- `notebook/run_simulation.py`: Runs a scripted simulation and creates plots.
- `tests/test_model.py`: Contains regression tests for the model behavior.

## Further Reading

This example is inspired by zero-intelligence trader models of double-auction
markets, especially:

Gode, D. K., & Sunder, S. (1993). Allocative efficiency of markets with
zero-intelligence traders: Market as a partial substitute for individual
rationality. _Journal of Political Economy_, 101(1), 119-137.
