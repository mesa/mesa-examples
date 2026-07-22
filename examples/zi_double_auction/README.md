# Continuous Double Auction (ZI-C) Market Model

## Overview

This model implements a Continuous Double Auction (CDA) — the kind of matching
engine that underlies most real financial exchanges — populated by simple,
randomized "Zero-Intelligence" traders (following Gode & Sunder's ZI-C
formulation). It reproduces their classic 1993 result: even traders with no
strategy or market knowledge, constrained only by a private valuation, will
drive a market toward its theoretical equilibrium price purely through the
mechanics of the auction itself.

Beyond the economics, this example showcases Mesa's continuous-time,
event-driven scheduling. Traders don't act in lockstep on a fixed tick —
each schedules its own next arrival at a randomized, staggered `model.time`,
rather than all acting on every discrete step.

## Gode & Sunder ZI-C Traders

Each trader (`Buyer` or `Seller`) is assigned a private value on creation —
a buyer's maximum willingness to pay, or a seller's minimum acceptable cost.
On arrival, a trader cancels any stale resting order of its own, then submits
a new random order constrained by that private value:

- **Buyers** submit a bid drawn uniformly from `[0, private_value]`
- **Sellers** submit an ask drawn uniformly from `[private_value, max_valuation]`

No trader ever sees the order book, other traders, or market history — all
convergence toward equilibrium emerges purely from the auction mechanism,
not from trader intelligence.

## How It Works

1. **Arrival**: Each trader schedules its own first arrival on creation, then
   repeated arrivals via `model.rng.exponential(mean_interarrival)` — a
   randomized, staggered delay rather than a fixed tick.
2. **Order submission**: On arrival, the trader cancels any stale resting
   order of its own, then submits a new random bid/ask as described above.
3. **Matching**: The order book matches on price-time priority — best bid is
   the highest price (earliest timestamp breaks ties), best ask is the
   lowest price (earliest timestamp breaks ties).
4. **Clearing**: Whenever the best bid crosses the best ask
   (`best_bid.price >= best_ask.price`), the trade clears at their exact
   midpoint: `(best_bid.price + best_ask.price) / 2`.
5. **Full clearing per arrival**: After each new order, `handle_arrival`
   matches in a loop until no crossing orders remain — this was fixed after
   review caught that a single match per arrival could leave the book still
   crossed.
6. **Data collection**: Every tick, `DataCollector` records `ClearingPrice`,
   `Volume`, `CumulativeVolume`, `Spread`, `BestBid`, and `BestAsk` at the
   model level, and `Wealth`, `Cash`, `Inventory`, `PrivateValue`, `Type`,
   and `DoneTrading` at the agent level.

## Installation

Install dependencies from this example's `requirements.txt`:

```bash
pip install -r requirements.txt
```

which pins:

```text
mesa[viz]>=3.5
pandas
matplotlib
pytest
```

(Tested against both Mesa 3.5.1 and the Mesa 4.0 development branch.)

## Running the Model

**Interactively**, from the repository root:

```bash
solara run examples/zi_double_auction/notebook/app.py
```

or, from inside `examples/zi_double_auction/`:

```bash
solara run notebook/app.py
```

Then open your browser to the local Solara URL, select model parameters,
press Reset, then Start, to view the live dashboard tracking clearing price,
spread, and volume in real time.

**As a scripted run**, from inside `examples/zi_double_auction/`:

```bash
python notebook/run_simulation.py
```

This prints recent model data, compares transaction prices against a
uniform-price equilibrium reference computed from the sampled private
values, and saves a summary figure to `notebook/simulation_results.png`.

## Project Structure

```plaintext
examples/zi_double_auction/
├── README.md
├── requirements.txt
├── model/
│   ├── __init__.py       # exports Buyer, Seller, Trader, DoubleAuctionModel, Order, OrderBook, Trade
│   ├── agents.py          # Trader base class, Buyer and Seller subclasses
│   ├── model.py            # DoubleAuctionModel: agent creation, DataCollector, handle_arrival
│   └── order_book.py       # Order, Trade dataclasses; OrderBook matching engine
├── notebook/
│   ├── app.py              # interactive SolaraViz dashboard
│   ├── run_simulation.py   # scripted run + summary plots
│   └── simulation_results.png
└── tests/
    ├── test_model.py        # integration tests: agent counts, inventories, timing, no-loss trades
    └── test_orderbook.py    # unit tests: matching, price-time priority, cancellation, spread
```

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `n_buyers` | `int` | `25` | Number of `Buyer` agents created |
| `n_sellers` | `int` | `25` | Number of `Seller` agents created |
| `max_valuation` | `float` | `100.0` | Upper bound for sampling buyer reservation prices, seller costs, and seller ask prices |
| `mean_interarrival` | `float` | `1.0` | Mean of the exponential distribution controlling how staggered trader arrival times are |
| `rng` | `int \| None` | `None` | Seed for Mesa's random number generator |

## Verification

The order book's matching engine is covered independently of Mesa in
`tests/test_orderbook.py` (price-time priority, tie-breaking, midpoint
clearing, cancellation, multi-trade clearing). `tests/test_model.py` adds
integration-level invariant checks — including that no agent ever transacts
at a loss relative to its private value, and that a trader with a completed
trade never reappears in the order book. The scripted run
(`run_simulation.py`) additionally verifies empirically that simulated
transaction prices converge toward the theoretical equilibrium price implied
by the sampled supply/demand curves, consistent with the original Gode &
Sunder result.

## Further Reading

Gode, D. K., & Sunder, S. (1993). Allocative Efficiency of Markets with
Zero-Intelligence Traders: Market as a Partial Substitute for Individual
Rationality. *Journal of Political Economy*, 101(1), 119–137.