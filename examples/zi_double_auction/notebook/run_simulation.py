import os
import sys

import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from model import DoubleAuctionModel


def theoretical_equilibrium(model: DoubleAuctionModel):
    """Compute a uniform-price equilibrium reference from private values."""

    buyers = [a for a in model.agents if type(a).__name__ == "Buyer"]
    sellers = [a for a in model.agents if type(a).__name__ == "Seller"]

    demand = sorted((b.private_value for b in buyers), reverse=True)
    supply = sorted(s.private_value for s in sellers)

    eq_qty = 0
    for q in range(1, min(len(demand), len(supply)) + 1):
        if demand[q - 1] >= supply[q - 1]:
            eq_qty = q
        else:
            break

    eq_price = (demand[eq_qty - 1] + supply[eq_qty - 1]) / 2 if eq_qty > 0 else None
    return demand, supply, eq_qty, eq_price


def run(
    n_buyers=25,
    n_sellers=25,
    max_valuation=100.0,
    mean_interarrival=1.0,
    duration=300,
    rng=42,
):
    """Run the model for a fixed duration and return model and data frames."""

    model = DoubleAuctionModel(
        n_buyers=n_buyers,
        n_sellers=n_sellers,
        max_valuation=max_valuation,
        mean_interarrival=mean_interarrival,
        rng=rng,
    )
    model.run_for(duration)

    model_df = model.datacollector.get_model_vars_dataframe()
    agent_df = model.datacollector.get_agent_vars_dataframe()
    return model, model_df, agent_df


def plot_results(model, model_df, save_path="simulation_results.png"):
    """Plot equilibrium, transaction prices, cumulative volume, and spread."""

    demand, supply, eq_qty, eq_price = theoretical_equilibrium(model)

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    # --- Panel 1: Supply & demand with theoretical equilibrium ---
    ax = axes[0]
    ax.step(
        range(1, len(demand) + 1),
        demand,
        where="post",
        label="Demand",
        color="tab:blue",
    )
    ax.step(
        range(1, len(supply) + 1), supply, where="post", label="Supply", color="tab:red"
    )
    if eq_price is not None:
        ax.axhline(
            eq_price,
            color="gray",
            linestyle="--",
            linewidth=1,
            label=f"Theoretical eq. price = {eq_price:.1f}",
        )
        ax.axvline(eq_qty, color="gray", linestyle=":", linewidth=1)
    ax.set_xlabel("Quantity")
    ax.set_ylabel("Price")
    ax.set_title("Supply & Demand (known private values)")
    ax.legend(fontsize=8)

    # --- Panel 2: Transaction price convergence, by model TIME not step ---
    ax = axes[1]
    if model.price_history:
        times, prices = zip(*model.price_history)
        ax.plot(
            times,
            prices,
            marker="o",
            markersize=3,
            linewidth=1,
            color="tab:green",
            label="Transaction price",
        )
    if eq_price is not None:
        ax.axhline(
            eq_price,
            color="gray",
            linestyle="--",
            linewidth=1,
            label="Theoretical equilibrium",
        )
    ax.set_xlabel("Model time")
    ax.set_ylabel("Price")
    ax.set_title("Transaction Price Convergence (continuous time)")
    ax.legend(fontsize=8)

    # --- Panel 3: Cumulative volume and spread, by tick ---
    ax = axes[2]
    ax.plot(
        model_df.index,
        model_df["CumulativeVolume"],
        color="tab:purple",
        label="Cumulative volume",
    )
    ax2 = ax.twinx()
    ax2.plot(
        model_df.index,
        model_df["Spread"],
        color="tab:orange",
        linewidth=1,
        label="Spread",
    )
    ax.set_xlabel("Tick (1 tick = 1 time unit)")
    ax.set_ylabel("Cumulative volume", color="tab:purple")
    ax2.set_ylabel("Bid-ask spread", color="tab:orange")
    ax.set_title("Volume & Spread")

    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    print(f"Saved figure to {save_path}")

    if eq_price is not None and model.price_history:
        last_5 = sum(p for _, p in model.price_history[-5:]) / min(
            5, len(model.price_history)
        )
        print(f"Theoretical equilibrium price: {eq_price:.2f} at quantity {eq_qty}")
        print(f"Mean of last 5 transaction prices: {last_5:.2f}")
        print(
            f"Absolute deviation: {abs(last_5 - eq_price):.2f} "
            f"({100 * abs(last_5 - eq_price) / eq_price:.1f}% of eq. price)"
        )
        print(
            f"Actual trades executed: {model.cumulative_volume} "
            f"(uniform-price equilibrium quantity: {eq_qty})"
        )


if __name__ == "__main__":
    model, model_df, agent_df = run(
        n_buyers=25,
        n_sellers=25,
        max_valuation=100.0,
        mean_interarrival=1.0,
        duration=300,
        rng=42,
    )
    print(model_df.tail(10))
    plot_results(
        model,
        model_df,
        save_path=os.path.join(os.path.dirname(__file__), "simulation_results.png"),
    )
