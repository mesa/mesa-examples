import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import solara
import solara.lab

from .model import MisinformationModel, RuleBasedMisinformationModel

matplotlib.use("Agg")

# Reactive state
n_believers = solara.reactive(4)
n_skeptics = solara.reactive(3)
n_spreaders = solara.reactive(2)
connectivity = solara.reactive(0.3)
n_steps = solara.reactive(5)

llm_data = solara.reactive(None)
rb_data = solara.reactive(None)
is_running = solara.reactive(False)
status_message = solara.reactive("Configure parameters and click Run.")


# Helper: run one model and return its dataframe
def run_model(use_llm: bool) -> pd.DataFrame:
    if use_llm:
        model = MisinformationModel(
            n_believers=n_believers.value,
            n_skeptics=n_skeptics.value,
            n_spreaders=n_spreaders.value,
            connectivity=connectivity.value,
            use_llm=True,
            rng=42,
        )
    else:
        model = RuleBasedMisinformationModel(
            n_believers=n_believers.value,
            n_skeptics=n_skeptics.value,
            n_spreaders=n_spreaders.value,
            connectivity=connectivity.value,
            rng=42,
        )

    for _ in range(n_steps.value):
        model.step()

    return model.datacollector.get_model_vars_dataframe()


# Chart components
@solara.component
def SpreadLineChart():
    llm = llm_data.value
    rb = rb_data.value

    if llm is None and rb is None:
        solara.Text("No data yet — run a simulation to see results.")
        return

    fig, ax = plt.subplots(figsize=(7, 4))

    if llm is not None:
        ax.plot(
            llm.index,
            llm["Spread Count"],
            label="LLM agents",
            color="steelblue",
            linewidth=2,
            marker="o",
        )
    if rb is not None:
        ax.plot(
            rb.index,
            rb["Spread Count"],
            label="Rule-based agents",
            color="coral",
            linewidth=2,
            marker="o",
            linestyle="--",
        )

    ax.set_title("Spread Count Over Time", fontweight="bold")
    ax.set_xlabel("Step")
    ax.set_ylabel("Cumulative Spread Count")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    solara.FigureMatplotlib(fig)
    plt.close(fig)


@solara.component
def FinalCountBarChart():
    llm = llm_data.value
    rb = rb_data.value

    if llm is None and rb is None:
        return

    categories = ["Believers", "Skeptics", "Spreaders"]
    fig, ax = plt.subplots(figsize=(6, 4))
    x = range(len(categories))
    width = 0.35

    if llm is not None:
        llm_final = [
            llm["Believers Convinced"].iloc[-1],
            llm["Skeptics Convinced"].iloc[-1],
            llm["Spreaders Active"].iloc[-1],
        ]
        ax.bar(
            [i - width / 2 for i in x],
            llm_final,
            width,
            label="LLM agents",
            color="steelblue",
            alpha=0.8,
        )

    if rb is not None:
        rb_final = [
            rb["Believers Convinced"].iloc[-1],
            rb["Skeptics Convinced"].iloc[-1],
            rb["Spreaders Active"].iloc[-1],
        ]
        ax.bar(
            [i + width / 2 for i in x],
            rb_final,
            width,
            label="Rule-based agents",
            color="coral",
            alpha=0.8,
        )

    ax.set_title("Final Convinced Count by Agent Type", fontweight="bold")
    ax.set_xlabel("Agent Type")
    ax.set_ylabel("Count")
    ax.set_xticks(list(x))
    ax.set_xticklabels(categories)
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.4, axis="y")
    plt.tight_layout()
    solara.FigureMatplotlib(fig)
    plt.close(fig)


@solara.component
def StepByStepTable():
    llm = llm_data.value
    rb = rb_data.value

    if llm is None and rb is None:
        return

    with solara.Row():
        if llm is not None:
            with solara.Column():
                solara.Text("LLM Model — Step Data", style="font-weight:bold")
                solara.DataFrame(llm.reset_index().rename(columns={"index": "Step"}))

        if rb is not None:
            with solara.Column():
                solara.Text("Rule-Based Model — Step Data", style="font-weight:bold")
                solara.DataFrame(rb.reset_index().rename(columns={"index": "Step"}))


# Sidebar controls
@solara.component
def Controls():
    solara.Text("Agent Counts", style="font-weight:bold; margin-top:8px")
    solara.SliderInt("Believers", value=n_believers, min=1, max=20)
    solara.SliderInt("Skeptics", value=n_skeptics, min=1, max=20)
    solara.SliderInt("Spreaders", value=n_spreaders, min=1, max=10)

    solara.Text("Network", style="font-weight:bold; margin-top:16px")
    solara.SliderFloat("Connectivity", value=connectivity, min=0.05, max=1.0, step=0.05)

    solara.Text("Simulation", style="font-weight:bold; margin-top:16px")
    solara.SliderInt("Steps", value=n_steps, min=1, max=30)

    solara.Text(
        "⚠️ LLM mode: ~10–30s per step (Ollama llama3)",
        style="color: #b45309; font-size:0.8rem; margin-top:8px",
    )

    def run_both():
        is_running.set(True)
        status_message.set("Running rule-based model...")
        rb_data.set(run_model(use_llm=False))
        status_message.set(f"Running LLM model ({n_steps.value} steps × ~15s each)...")
        llm_data.set(run_model(use_llm=True))
        is_running.set(False)
        status_message.set("Done! Adjust parameters and re-run to compare.")

    def run_rb_only():
        is_running.set(True)
        status_message.set("Running rule-based model...")
        rb_data.set(run_model(use_llm=False))
        is_running.set(False)
        status_message.set("Rule-based run complete.")

    solara.Button(
        "▶ Run Both Models",
        on_click=run_both,
        disabled=is_running.value,
        color="primary",
        style="margin-top:16px; width:100%",
    )
    solara.Button(
        "▶ Rule-Based Only (fast)",
        on_click=run_rb_only,
        disabled=is_running.value,
        style="margin-top:8px; width:100%",
    )

    solara.Text(
        status_message.value,
        style="margin-top:12px; font-size:0.85rem; color:#374151",
    )


# Main page
@solara.component
def Page():
    with solara.AppBar():
        solara.Text(
            "Misinformation Spread — LLM vs Rule-Based",
            style="font-size:1.1rem; font-weight:bold",
        )

    with solara.Sidebar():
        Controls()

    with solara.Column(style="padding: 24px"):
        solara.Text(
            "How do personality types shape misinformation dynamics?",
            style="font-size:1.05rem; color:#6b7280; margin-bottom:16px",
        )

        with solara.lab.Tabs():
            with solara.lab.Tab("Spread Over Time"):
                SpreadLineChart()

            with solara.lab.Tab("Final Counts"):
                FinalCountBarChart()

            with solara.lab.Tab("Raw Data"):
                StepByStepTable()
