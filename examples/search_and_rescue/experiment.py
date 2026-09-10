"""Parameter sweep over crew size and specialist policy.

Runs the model across a grid of design points with replications, using Mesa's
scenarios runner. The execution backend is pluggable: pass ``--sequential`` to
run in this process, or let it default to a ``ProcessPoolExecutor``. Both
produce identical results, which is the point of the abstraction.

Usage::

    python experiment.py                 # process pool, writes results/policy_comparison.png
    python experiment.py --sequential    # same sweep, single process
    python experiment.py --compare       # run both backends and assert they agree
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from mesa.experimental.scenarios import RunConfiguration, run_scenarios
from sar import SARScenario, SearchAndRescueModel

CREW_SIZES = (2, 3, 4, 5, 6, 8)
POLICIES = (True, False)
REPLICATIONS = 20
UNTIL = 150.0
RESULTS_DIR = Path(__file__).parent / "results"


def build_design() -> pd.DataFrame:
    """One row per design point: crew size crossed with specialist policy."""
    return pd.DataFrame(
        [
            {"crew_size": crew_size, "pooled_specialists": pooled}
            for crew_size in CREW_SIZES
            for pooled in POLICIES
        ]
    )


def run_sweep(executor=None) -> pd.DataFrame:
    """Run the full design and return one summary row per run."""
    scenarios = SARScenario.from_dataframe(
        build_design(), rng=42, replications=REPLICATIONS
    )
    config = RunConfiguration(SearchAndRescueModel, until=UNTIL, outcomes=["response"])
    store = run_scenarios(scenarios, config, executor=executor)

    failures = store.failed()
    if failures:
        for run_id, record in failures.items():
            print(
                f"FAILED {run_id}: {record.failure.exception_type} "
                f"{record.failure.message}"
            )
        raise RuntimeError(f"{len(failures)} runs failed")

    rows = []
    for run_id, record in store.succeeded().items():
        final = store.retrieve_output(run_id)["response"].iloc[-1]
        rows.append(
            {
                "crew_size": record.scenario.crew_size,
                "pooled_specialists": record.scenario.pooled_specialists,
                "replication": run_id.replication_id,
                "rescued": int(final["rescued"]),
                "lost": int(final["lost"]),
                "span_of_control": int(final["span_of_control"]),
                "medic_handoffs": int(final["medic_handoffs"]),
            }
        )
    return pd.DataFrame(rows)


def plot(summary: pd.DataFrame) -> Path:
    """Draw the policy comparison and the span-of-control tradeoff."""
    grouped = summary.groupby(["crew_size", "pooled_specialists"])
    mean = grouped.mean(numeric_only=True).reset_index()
    error = grouped.sem(numeric_only=True).reset_index()

    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 4.2))

    for pooled, label, colour in (
        (True, "pooled specialists", "#1b6ca8"),
        (False, "embedded specialists", "#b8532a"),
    ):
        rows = mean[mean.pooled_specialists == pooled]
        bars = error[error.pooled_specialists == pooled]
        left.errorbar(
            rows.crew_size,
            rows.rescued,
            yerr=bars.rescued,
            marker="o",
            capsize=3,
            label=label,
            color=colour,
        )

    left.set_xlabel("crew size")
    left.set_ylabel(f"victims rescued by t={UNTIL:g}")
    left.set_title("Pooling scarce medics beats embedding them")
    left.legend()
    left.grid(alpha=0.3)

    pooled_rows = mean[mean.pooled_specialists]
    right.plot(
        pooled_rows.crew_size,
        pooled_rows.span_of_control,
        marker="s",
        color="#3b7a57",
    )
    right.set_xlabel("crew size")
    right.set_ylabel("units reporting to incident command")
    right.set_title("Smaller crews rescue more, but widen span of control")
    right.grid(alpha=0.3)

    fig.tight_layout()
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / "policy_comparison.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def report(summary: pd.DataFrame) -> None:
    """Print the headline numbers behind the figure."""
    table = (
        summary.groupby(["crew_size", "pooled_specialists"])[
            ["rescued", "lost", "span_of_control", "medic_handoffs"]
        ]
        .mean()
        .round(2)
    )
    print(table.to_string())

    pooled = summary[summary.pooled_specialists].groupby("crew_size").rescued.mean()
    embedded = summary[~summary.pooled_specialists].groupby("crew_size").rescued.mean()
    delta = (pooled - embedded).round(2)
    print("\nAdditional rescues from pooling, by crew size:")
    print(delta.to_string())


def main() -> None:
    """Run the sweep and write the figure."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sequential", action="store_true", help="run in this process")
    parser.add_argument(
        "--compare",
        action="store_true",
        help="run both backends and check they agree",
    )
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    if args.compare:
        sequential = run_sweep(executor=None)
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            parallel = run_sweep(executor=pool)
        key = ["crew_size", "pooled_specialists", "replication"]
        merged = sequential.merge(parallel, on=key, suffixes=("_seq", "_par"))
        assert len(merged) == len(sequential), "run sets differ between backends"
        mismatched = merged[merged.rescued_seq != merged.rescued_par]
        print(
            f"compared {len(merged)} runs across both execution backends; "
            f"{len(mismatched)} mismatched"
        )
        assert mismatched.empty, "execution backends disagree"
        summary = sequential
    elif args.sequential:
        summary = run_sweep(executor=None)
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            summary = run_sweep(executor=pool)

    report(summary)
    print(f"\nwrote {plot(summary)}")


if __name__ == "__main__":
    main()
