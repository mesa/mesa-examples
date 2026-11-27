import logging
import warnings

import matplotlib.pyplot as plt
import pandas as pd
import solara
from climate_negotiation.agents import CountryAgent
from climate_negotiation.model import ClimateNegotiationModel
from dotenv import load_dotenv
from mesa.visualization import SolaraViz, make_plot_component
from mesa.visualization.utils import update_counter
from mesa_llm.reasoning.react import ReActReasoning

warnings.filterwarnings("ignore", category=UserWarning, module="pydantic.main")
logging.getLogger("pydantic").setLevel(logging.ERROR)

load_dotenv()

model_params = {
    "rng": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "llm_model": {
        "type": "Select",
        "value": "gemini/gemini-2.0-flash",
        "values": [
            "gemini/gemini-2.0-flash",
            "openai/gpt-4o-mini",
            "openai/gpt-4o",
            "anthropic/claude-haiku-4-5-20251001",
            "ollama/llama3.2",
        ],
        "label": "LLM Model",
    },
    "reasoning": ReActReasoning,
}

model = ClimateNegotiationModel(
    reasoning=model_params["reasoning"],
    llm_model=model_params["llm_model"]["value"],
    rng=model_params["rng"]["value"],
)


def PledgeBarChart(model):
    """Bar chart of each country's current reduction pledge."""
    update_counter.get()

    countries = [a for a in model.agents if isinstance(a, CountryAgent)]

    fig, ax = plt.subplots(figsize=(8, 4))

    if not countries or all(a.current_pledge == 0 for a in countries):
        ax.set_title("No pledges yet — click Step to begin")
        ax.set_ylim(0, 100)
        return solara.FigureMatplotlib(fig)

    names = [a.country_name for a in countries]
    pledges = [a.current_pledge for a in countries]
    colors = ["#27ae60" if a.accepted_treaty else "#2980b9" for a in countries]

    bars = ax.bar(names, pledges, color=colors, edgecolor="white", linewidth=0.8)
    ax.axhline(y=30, color="#e67e22", linestyle="--", linewidth=1.4, label="30% target")
    ax.axhline(y=50, color="#e74c3c", linestyle="--", linewidth=1.4, label="50% target")
    ax.set_ylabel("Reduction Pledge (%)", fontsize=11)
    ax.set_title(
        f"Country Pledges (green = accepted treaty) — Round {model.steps}", fontsize=12
    )
    ax.set_ylim(0, 100)
    ax.legend(loc="upper right", fontsize=9)

    for bar, pledge in zip(bars, pledges):
        if pledge > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1.2,
                f"{pledge:.0f}%",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
            )

    plt.tight_layout()
    return solara.FigureMatplotlib(fig)


@solara.component
def CoalitionStatusPanel(model):
    update_counter.get()

    countries = [a for a in model.agents if isinstance(a, CountryAgent)]
    id_to_name = {a.unique_id: a.country_name for a in countries}
    treaty_count = sum(1 for a in countries if a.accepted_treaty)
    treaty_reached = model._treaty_reached()

    solara.Text(
        f"Round {model.steps}  ·  "
        f"Accepted: {treaty_count}/{len(countries)}  ·  "
        f"Treaty: {'YES ✓' if treaty_reached else 'not yet'}  ·  "
        f"Proposals: {model.total_proposals}  ·  "
        f"Avg pledge: {model._average_pledge():.1f}%"
    )

    rows = []
    for a in sorted(countries, key=lambda x: x.country_name):
        coalition = [id_to_name.get(i, str(i)) for i in a.coalition_members]
        rows.append(
            {
                "Country": a.country_name,
                "Pledge": f"{a.current_pledge:.1f}%",
                "Accepted": "✓" if a.accepted_treaty else "—",
                "Coalition": ", ".join(coalition) or "—",
                "Proposals": a.proposals_made,
            }
        )

    solara.DataFrame(pd.DataFrame(rows))


def PledgeTrajectoriesChart(model):
    """Line chart of pledge trajectories over rounds."""
    update_counter.get()

    fig, ax = plt.subplots(figsize=(8, 4))

    try:
        df = model.datacollector.get_agent_vars_dataframe()
    except Exception:
        ax.set_title("No trajectory data yet")
        return solara.FigureMatplotlib(fig)

    if df.empty or "CurrentPledge" not in df.columns:
        ax.set_title("No trajectory data yet — run a few steps")
        return solara.FigureMatplotlib(fig)

    id_to_name = {
        a.unique_id: a.country_name for a in model.agents if isinstance(a, CountryAgent)
    }

    if isinstance(df.index, pd.MultiIndex):
        pledge_df = df["CurrentPledge"].unstack(level=1)
        pledge_df.columns = [id_to_name.get(c, str(c)) for c in pledge_df.columns]
    else:
        ax.set_title("Run more steps to see trajectories")
        return solara.FigureMatplotlib(fig)

    for country in pledge_df.columns:
        ax.plot(
            pledge_df.index, pledge_df[country], marker="o", label=country, linewidth=2
        )

    ax.set_xlabel("Round", fontsize=11)
    ax.set_ylabel("Reduction Pledge (%)", fontsize=11)
    ax.set_title("Pledge Trajectories by Country", fontsize=12)
    ax.legend(loc="upper left", fontsize=9)
    ax.set_ylim(0, 100)
    plt.tight_layout()
    return solara.FigureMatplotlib(fig)


TotalProposalsPlot = make_plot_component("TotalProposals")
AveragePledgePlot = make_plot_component("AveragePledge")
LargestCoalitionPlot = make_plot_component("LargestCoalitionSize")

# renderer=None: no spatial grid in this model, so we skip the default space view
page = SolaraViz(
    model,
    renderer=None,
    components=[
        PledgeBarChart,
        CoalitionStatusPanel,
        PledgeTrajectoriesChart,
        TotalProposalsPlot,
        AveragePledgePlot,
        LargestCoalitionPlot,
    ],
    model_params=model_params,
    name="Climate Negotiation - Mesa-LLM",
)
