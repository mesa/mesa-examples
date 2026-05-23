import solara
from matplotlib.figure import Figure
from mesa.visualization import Slider, SolaraViz, SpaceRenderer
from mesa.visualization.components.portrayal_components import AgentPortrayalStyle
from ratchet_effect.model import RatchetEffectModel


def worker_portrayal(agent):
    """Color workers by work mode; size reflects accumulated lock-in.

    Remote workers (green): larger = more locked in, harder to return.
    Office workers (blue): uniform small size, low lock-in by definition.
    """
    if agent is None:
        return

    if agent.work_mode == "remote":
        # Green gradient: light green (new remote) → deep green (fully locked in)
        g = int(120 + 135 * agent.lock_in)
        r = int(60 - 60 * agent.lock_in)
        b = int(60 - 60 * agent.lock_in)
        color = f"#{max(0, r):02x}{min(255, g):02x}{max(0, b):02x}"
        size = 90 + int(110 * agent.lock_in)
    else:
        # Steel blue for office workers
        color = "#3a7abf"
        size = 80

    return AgentPortrayalStyle(color=color, size=size, marker="s", zorder=1)


def post_process_space(ax):
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect("equal")
    ax.get_figure().set_size_inches(7, 7)


@solara.component
def RatchetChart(model):
    """Time-series chart showing remote % and return resistance with shock shading."""
    fig = Figure(figsize=(9, 4), dpi=100)
    ax = fig.subplots()

    df = model.datacollector.get_model_vars_dataframe()
    if df.empty:
        solara.FigureMatplotlib(fig)
        return

    steps = df.index.tolist()
    remote_pct = df["Remote Workers (%)"].tolist()
    resistance = df["Return Resistance"].tolist()
    shock_flags = df["Shock"].tolist()

    ax.plot(steps, remote_pct, color="#27ae60", linewidth=2, label="Remote Workers (%)")
    ax.plot(
        steps,
        [r * 100 for r in resistance],
        color="#e74c3c",
        linewidth=1.5,
        linestyle="--",
        label="Return Resistance (x100)",
    )

    # Shade shock period
    shock_on = [s for s, f in zip(steps, shock_flags) if f == 1]
    if shock_on:
        ax.axvspan(
            min(shock_on) - 0.5,
            max(shock_on) + 0.5,
            alpha=0.15,
            color="#e67e22",
            label="Shock period",
        )

    ax.set_xlabel("Step")
    ax.set_ylabel("Value")
    ax.set_title("Remote Work Adoption & Return Resistance Over Time")
    ax.legend(loc="upper left")
    ax.set_ylim(0, 105)
    fig.tight_layout()

    solara.FigureMatplotlib(fig)


@solara.component
def LockInChart(model):
    """Chart showing average lock-in across all workers over time."""
    fig = Figure(figsize=(9, 3), dpi=100)
    ax = fig.subplots()

    df = model.datacollector.get_model_vars_dataframe()
    if df.empty:
        solara.FigureMatplotlib(fig)
        return

    ax.plot(
        df.index,
        df["Avg Lock-in"],
        color="#8e44ad",
        linewidth=2,
        label="Avg Lock-in",
    )
    ax.fill_between(df.index, df["Avg Lock-in"], alpha=0.2, color="#8e44ad")
    ax.set_xlabel("Step")
    ax.set_ylabel("Lock-in (0-1)")
    ax.set_title("Average Lock-in Accumulation")
    ax.set_ylim(0, 1.05)
    ax.legend()
    fig.tight_layout()

    solara.FigureMatplotlib(fig)


model_params = {
    "n_workers": Slider("Number of Workers", 100, 20, 200, 10),
    "initial_remote_fraction": Slider("Initial Remote Fraction", 0.05, 0.0, 0.5, 0.05),
    "adaptation_rate": Slider("Adaptation Rate (→ remote)", 0.025, 0.005, 0.15, 0.005),
    "return_rate": Slider("Return Rate Factor (→ office)", 0.35, 0.05, 0.6, 0.05),
    "social_influence": Slider("Social Influence", 0.35, 0.0, 1.0, 0.05),
    "employer_remote_openness": Slider("Employer Remote Openness", 0.2, 0.0, 1.0, 0.05),
    "shock_step": Slider("Shock Step (0 = no shock)", 30, 0, 80, 5),
    "shock_duration": Slider("Shock Duration (steps)", 8, 1, 20, 1),
    "width": 15,
    "height": 15,
    "rng": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
}

model = RatchetEffectModel()

renderer = SpaceRenderer(model, backend="matplotlib").setup_agents(worker_portrayal)
renderer.post_process = post_process_space
renderer.draw_agents()

page = SolaraViz(
    model,
    renderer,
    components=[RatchetChart, LockInChart],
    model_params=model_params,
    name="The Ratchet Effect — Remote Work",
)

page  # noqa
