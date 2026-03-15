import matplotlib.pyplot as plt
from model import PollinatorCascadeModel

N_POLLINATORS = 20
N_PLANTS = 30
CONNECTIVITY = 0.35
STEPS = 150
EXTINCTION_SCHEDULE = [30, 60, 90]
SEED = 42

print("Initializing model...")
model = PollinatorCascadeModel(
    n_pollinators=N_POLLINATORS,
    n_plants=N_PLANTS,
    connectivity=CONNECTIVITY,
    extinction_schedule=EXTINCTION_SCHEDULE,
    rng=SEED,
)
print(
    f"Network: {N_POLLINATORS} pollinators, "
    f"{N_PLANTS} plants, connectivity={CONNECTIVITY}"
)
print(f"Extinction schedule: steps {EXTINCTION_SCHEDULE}")
print(f"Running for {STEPS} steps...\n")

for step in range(STEPS):
    model.step()
    if (step + 1) % 10 == 0:
        alive_p = sum(1 for a in model.agents if hasattr(a, "energy") and a.alive)
        alive_pl = sum(1 for a in model.agents if hasattr(a, "health") and a.alive)
        print(
            f"Step {step + 1:3d} | "
            f"Pollinators: {alive_p:3d} | "
            f"Plants: {alive_pl:3d}"
        )

model_data = model.datacollector.get_model_vars_dataframe()

print("\nModel run complete.")
print(f"Final alive pollinators: " f"{model_data['Alive Pollinators'].iloc[-1]:.2%}")
print(f"Final alive plants:      " f"{model_data['Alive Plants'].iloc[-1]:.2%}")
print(f"Total plant deaths:      " f"{int(model_data['Cascade Depth'].iloc[-1])}")


def plot_results(model_data, extinction_schedule):
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(
        "Pollinator-Plant Cascade Extinction Model", fontsize=14, fontweight="bold"
    )

    # Panel 1: Survival rates for both species
    axes[0].plot(
        model_data.index,
        model_data["Alive Pollinators"],
        label="Pollinators",
        color="steelblue",
        linewidth=2,
    )
    axes[0].plot(
        model_data.index,
        model_data["Alive Plants"],
        label="Plants",
        color="forestgreen",
        linewidth=2,
    )
    for step in extinction_schedule:
        axes[0].axvline(
            x=step,
            color="red",
            linestyle="--",
            alpha=0.5,
            label="Extinction shock" if step == extinction_schedule[0] else "",
        )
    axes[0].set_title("Survival Rates Over Time")
    axes[0].set_xlabel("Step")
    axes[0].set_ylabel("Fraction Alive")
    axes[0].legend()
    axes[0].set_ylim(0, 1.1)

    # Panel 2: Cumulative plant deaths over time
    axes[1].fill_between(
        model_data.index, model_data["Cascade Depth"], alpha=0.6, color="coral"
    )
    axes[1].plot(
        model_data.index, model_data["Cascade Depth"], color="coral", linewidth=2
    )
    for step in extinction_schedule:
        axes[1].axvline(x=step, color="red", linestyle="--", alpha=0.5)
    axes[1].set_title("Cascade Depth (Cumulative Plant Deaths)")
    axes[1].set_xlabel("Step")
    axes[1].set_ylabel("Total Plants Dead")

    # Panel 3: Difference in survival rates between species
    # Negative = plants dying faster = cascade in effect
    lag = model_data["Alive Pollinators"] - model_data["Alive Plants"]
    axes[2].plot(model_data.index, lag, color="purple", linewidth=2)
    axes[2].axhline(y=0, color="black", linestyle="-", alpha=0.3)
    axes[2].fill_between(
        model_data.index,
        lag,
        0,
        where=(lag > 0),
        alpha=0.3,
        color="purple",
        label="Pollinators dying faster",
    )
    axes[2].fill_between(
        model_data.index,
        lag,
        0,
        where=(lag < 0),
        alpha=0.3,
        color="orange",
        label="Plants dying faster (cascade)",
    )
    axes[2].set_title("Pollinator-Plant Survival Gap")
    axes[2].set_xlabel("Step")
    axes[2].set_ylabel("Difference in Survival Rate")
    axes[2].legend()

    plt.tight_layout()
    plt.savefig("images/cascade_results.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("\nPlot saved to images/cascade_results.png")


plot_results(model_data, EXTINCTION_SCHEDULE)
