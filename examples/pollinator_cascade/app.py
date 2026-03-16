import solara
from matplotlib.figure import Figure
from mesa.visualization import SolaraViz, make_plot_component
from mesa.visualization.components import AgentPortrayalStyle
from mesa.visualization.utils import update_counter

try:
    from .model import PollinatorCascadeModel
    from .agents import Pollinator, Plant
except ImportError:
    from model import PollinatorCascadeModel
    from agents import Pollinator, Plant

model_params = {
    "n_pollinators": {
        "type": "SliderInt",
        "value": 20,
        "label": "Number of Pollinators",
        "min": 5,
        "max": 40,
        "step": 1,
    },
    "n_plants": {
        "type": "SliderInt",
        "value": 30,
        "label": "Number of Plants",
        "min": 10,
        "max": 60,
        "step": 1,
    },
    "connectivity": {
        "type": "SliderFloat",
        "value": 0.35,
        "label": "Network Connectivity",
        "min": 0.1,
        "max": 0.8,
        "step": 0.05,
    },
    "extinction_schedule": [30, 60, 90],
    "rng": 42,
}


def agent_portrayal(agent):
    # Pollinators: blue when healthy, red when low energy, gray when dead
    # Plants: green when healthy, yellow when declining, red when critical
    if isinstance(agent, Pollinator):
        if not agent.alive:
            return AgentPortrayalStyle(color="gray", size=20)
        elif agent.energy > 0.5:
            return AgentPortrayalStyle(color="steelblue", size=80)
        else:
            return AgentPortrayalStyle(color="red", size=40)

    elif isinstance(agent, Plant):
        if not agent.alive:
            return AgentPortrayalStyle(color="gray", size=20)
        elif agent.health > 0.7:
            return AgentPortrayalStyle(color="forestgreen", size=80)
        elif agent.health > 0.4:
            return AgentPortrayalStyle(color="gold", size=60)
        else:
            return AgentPortrayalStyle(color="red", size=40)

    return AgentPortrayalStyle(color="purple", size=30)


@solara.component
def EnergyHealthHistogram(model):
    # Shows distribution of pollinator energy and plant health
    # Rebuilt every step so the histogram reflects current state
    update_counter.get()

    fig = Figure(figsize=(8, 3))
    axes = fig.subplots(1, 2)

    energies = [a.energy for a in model.agents if isinstance(a, Pollinator) and a.alive]
    healths = [a.health for a in model.agents if isinstance(a, Plant) and a.alive]

    if energies:
        axes[0].hist(
            energies,
            bins=10,
            range=(0, 1),
            color="steelblue",
            alpha=0.7,
            edgecolor="white",
        )
    axes[0].set_title(f"Pollinator Energy Distribution\n({len(energies)} alive)")
    axes[0].set_xlabel("Energy")
    axes[0].set_ylabel("Count")
    axes[0].set_xlim(0, 1)

    if healths:
        axes[1].hist(
            healths,
            bins=10,
            range=(0, 1),
            color="forestgreen",
            alpha=0.7,
            edgecolor="white",
        )
    axes[1].set_title(f"Plant Health Distribution\n({len(healths)} alive)")
    axes[1].set_xlabel("Health")
    axes[1].set_ylabel("Count")
    axes[1].set_xlim(0, 1)

    fig.tight_layout()
    solara.FigureMatplotlib(fig)


def post_process_survival(ax):
    ax.set_title("Survival Rates Over Time")
    ax.set_xlabel("Step")
    ax.set_ylabel("Fraction Alive")
    ax.set_ylim(0, 1.1)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(["Pollinators", "Plants"])


def post_process_cascade(ax):
    ax.set_title("Cascade Depth (Cumulative Plant Deaths)")
    ax.set_xlabel("Step")
    ax.set_ylabel("Total Plants Dead")
    ax.grid(True, linestyle="--", alpha=0.4)


model = PollinatorCascadeModel(
    n_pollinators=20,
    n_plants=30,
    connectivity=0.35,
    extinction_schedule=[30, 60, 90],
    rng=42,
)

SurvivalPlot = make_plot_component(
    {"Alive Pollinators": "steelblue", "Alive Plants": "forestgreen"},
    post_process=post_process_survival,
    page=1,
)

CascadePlot = make_plot_component(
    "Cascade Depth",
    post_process=post_process_cascade,
    page=1,
)

page = SolaraViz(
    model,
    components=[
        SurvivalPlot,
        CascadePlot,
        (EnergyHealthHistogram, 2),
    ],
    model_params=model_params,
    name="Pollinator-Plant Cascade Extinction Model",
)

