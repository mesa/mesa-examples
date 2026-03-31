"""
Batch comparison: Original vs Monolith vs Behavioural Sugarscape.

Runs all three models across the same seeds and compares:
- Survival rate
- Trade volume
- Final price
- Drive distribution (monolith and behavioural only)

Outputs summary statistics and saves raw data to CSV.
"""

import sys
from pathlib import Path

sys.path.insert(
    0, "/Users/tomrodger/GSoC-learning-space/models/sugarscape/monolith")
sys.path.insert(
    0, "/Users/tomrodger/GSoC-learning-space/models/sugarscape/behavioural")

import pandas as pd
from behavioural_model import SugarscapeBehavioural
from mesa.examples.advanced.sugarscape_g1mt.model import SugarscapeG1mt
from monolith_model import SugarscapeMonolith

# Add subfolders to path so we can import from each
sys.path.insert(0, str(Path(__file__).parent / "monolith"))
sys.path.insert(0, str(Path(__file__).parent / "behavioural"))


# ---- Configuration ----
NUM_SEEDS = 100
STEPS = 500
INITIAL_POPULATION = 200


def run_model(model_class, seed):
    """Run a single model and return key metrics."""
    try:
        model = model_class(rng=seed)
        model.run_model(step_count=STEPS)
    except (ValueError, KeyError):
        # Original Mesa model has bugs with empty grids / datacollector
        return None

    data = model.datacollector.get_model_vars_dataframe()

    alive = len(model.agents)
    survival_rate = alive / INITIAL_POPULATION

    total_trade = data["Trade Volume"].sum()

    prices = data["Price"]
    valid_prices = prices[prices > 0]
    final_price = valid_prices.iloc[-1] if len(valid_prices) > 0 else -1

    return {
        "seed": seed,
        "alive": alive,
        "survival_rate": survival_rate,
        "total_trade": total_trade,
        "final_price": final_price,
    }


def run_batch(model_class, name):
    print(f"\nRunning {name}...")
    results = []
    for i, seed in enumerate(range(NUM_SEEDS)):
        if (i + 1) % 10 == 0:
            print(f"  {i + 1}/{NUM_SEEDS}")
        result = run_model(model_class, seed)
        if result is not None:
            results.append(result)
    print(f"  Completed: {len(results)}/{NUM_SEEDS} succeeded")
    df = pd.DataFrame(results)
    df["model"] = name
    return df


def print_summary(df, name):
    """Print summary statistics for a model's batch results."""
    print(f"\n{'='*50}")
    print(f"  {name} ({NUM_SEEDS} runs, {STEPS} steps)")
    print(f"{'='*50}")
    print(f"  Survival rate:  {df['survival_rate'].mean():.3f} "
          f"± {df['survival_rate'].std():.3f}")
    print(f"  Final alive:    {df['alive'].mean():.1f} "
          f"± {df['alive'].std():.1f}")
    print(f"  Total trades:   {df['total_trade'].mean():.1f} "
          f"± {df['total_trade'].std():.1f}")
    valid = df[df["final_price"] > 0]["final_price"]
    if len(valid) > 0:
        print(f"  Final price:    {valid.mean():.3f} "
              f"± {valid.std():.3f}")
    else:
        print("  Final price:    N/A")


def main():
    print(f"Batch comparison: {NUM_SEEDS} seeds, {STEPS} steps each")
    print("Models: Original, Monolith, Behavioural")

    # Run all three
    original_df = run_batch(SugarscapeG1mt, "Original")
    monolith_df = run_batch(SugarscapeMonolith, "Monolith")
    behavioural_df = run_batch(SugarscapeBehavioural, "Behavioural")

    # Print summaries
    print_summary(original_df, "Original")
    print_summary(monolith_df, "Monolith")
    print_summary(behavioural_df, "Behavioural")

    # Side-by-side comparison
    print(f"\n{'='*60}")
    print("  Side-by-Side Comparison")
    print(f"{'='*60}")
    print(f"{'Metric':<20} {'Original':>12} {'Monolith':>12} {'Behavioural':>12}")
    print(f"{'-'*56}")
    print(f"{'Survival rate':<20} "
          f"{original_df['survival_rate'].mean():>11.3f} "
          f"{monolith_df['survival_rate'].mean():>12.3f} "
          f"{behavioural_df['survival_rate'].mean():>12.3f}")
    print(f"{'Final alive':<20} "
          f"{original_df['alive'].mean():>11.1f} "
          f"{monolith_df['alive'].mean():>12.1f} "
          f"{behavioural_df['alive'].mean():>12.1f}")
    print(f"{'Total trades':<20} "
          f"{original_df['total_trade'].mean():>11.1f} "
          f"{monolith_df['total_trade'].mean():>12.1f} "
          f"{behavioural_df['total_trade'].mean():>12.1f}")

    # Save raw data
    all_data = pd.concat([original_df, monolith_df, behavioural_df])
    all_data.to_csv("batch_comparison.csv", index=False)
    print("\nRaw data saved to batch_comparison.csv")


if __name__ == "__main__":
    main()
