import matplotlib.pyplot as plt
from model import MisinformationModel, RuleBasedMisinformationModel

STEPS = 3
SEED = 42

# Run rule-based model
print("Running rule-based model...")
rb_model = RuleBasedMisinformationModel(
    n_believers=4,
    n_skeptics=3,
    n_spreaders=2,
    connectivity=0.3,
    rng=SEED,
)
for _ in range(STEPS):
    rb_model.step()

rb_data = rb_model.datacollector.get_model_vars_dataframe()
print("Rule-based model complete.")
print(rb_data)

# Run LLM model
print("\nRunning LLM-driven model...")
print("Note: each step takes 10-30 seconds due to LLM calls\n")

llm_model = MisinformationModel(
    n_believers=4,
    n_skeptics=3,
    n_spreaders=2,
    connectivity=0.3,
    use_llm=True,
    rng=SEED,
)

for step in range(STEPS):
    llm_model.step()
    df = llm_model.datacollector.get_model_vars_dataframe()
    believers = df["Believers Convinced"].iloc[-1]
    skeptics = df["Skeptics Convinced"].iloc[-1]
    spreaders = df["Spreaders Active"].iloc[-1]
    print(
        f"Step {step + 1} | "
        f"Believers: {int(believers)} | "
        f"Skeptics: {int(skeptics)} | "
        f"Spreaders: {int(spreaders)}"
    )

llm_data = llm_model.datacollector.get_model_vars_dataframe()
print("\nLLM model complete.")
print(llm_data)


def plot_comparison(llm_data, rb_data):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(
        "LLM vs Rule-Based Misinformation Spread", fontsize=14, fontweight="bold"
    )

    axes[0].plot(
        llm_data.index,
        llm_data["Spread Count"],
        label="LLM agents",
        color="steelblue",
        linewidth=2,
        marker="o",
    )
    axes[0].plot(
        rb_data.index,
        rb_data["Spread Count"],
        label="Rule-based agents",
        color="coral",
        linewidth=2,
        marker="o",
        linestyle="--",
    )
    axes[0].set_title("Spread Count Over Time")
    axes[0].set_xlabel("Step")
    axes[0].set_ylabel("Cumulative Spread Count")
    axes[0].legend()
    axes[0].grid(True, linestyle="--", alpha=0.4)

    categories = ["Believers", "Skeptics", "Spreaders"]
    llm_final = [
        llm_data["Believers Convinced"].iloc[-1],
        llm_data["Skeptics Convinced"].iloc[-1],
        llm_data["Spreaders Active"].iloc[-1],
    ]
    rb_final = [
        rb_data["Believers Convinced"].iloc[-1],
        rb_data["Skeptics Convinced"].iloc[-1],
        rb_data["Spreaders Active"].iloc[-1],
    ]

    x = range(len(categories))
    width = 0.35
    axes[1].bar(
        [i - width / 2 for i in x],
        llm_final,
        width,
        label="LLM agents",
        color="steelblue",
        alpha=0.8,
    )
    axes[1].bar(
        [i + width / 2 for i in x],
        rb_final,
        width,
        label="Rule-based agents",
        color="coral",
        alpha=0.8,
    )
    axes[1].set_title("Final Convinced Count by Agent Type")
    axes[1].set_xlabel("Agent Type")
    axes[1].set_ylabel("Count")
    axes[1].set_xticks(list(x))
    axes[1].set_xticklabels(categories)
    axes[1].legend()
    axes[1].grid(True, linestyle="--", alpha=0.4, axis="y")

    plt.tight_layout()
    plt.savefig("images/comparison_results.png", dpi=150, bbox_inches="tight")
    plt.show(block=False)
    plt.pause(0.1)
    print("\nPlot saved to images/comparison_results.png")


plot_comparison(llm_data, rb_data)
