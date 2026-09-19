"""
app.py — Solara visualisation for the Needs-Based Village model.

Run with:
    solara run app.py

Then open http://127.0.0.1:8765 in your browser.

The visualisation shows:
  - Grid: villagers coloured by dominant need, environment agents marked
  - Mean need levels over time (4 series)
  - Agent-count distribution by active need (stacked area)
  - Critical agents + cumulative preemptions (Pain Point #16)
"""

from mesa.visualization import SolaraViz, make_plot_component, make_space_component
from needs_village.agents import FoodSource, HomePatch, ThreatAgent, VillagerAgent
from needs_village.model import VillageModel

# ──────────────────────────────────────────────────────────────────────── #
#  Agent portrayal                                                         #
# ──────────────────────────────────────────────────────────────────────── #

_NEED_COLORS = {
    "HUNGER": "tab:orange",
    "REST": "tab:blue",
    "SOCIAL": "tab:green",
    "SAFETY": "tab:red",
}


def agent_portrayal(agent):
    """Map each agent to its visual properties."""
    if isinstance(agent, VillagerAgent):
        return {
            "color": _NEED_COLORS.get(agent._active_need or "HUNGER", "tab:gray"),
            "size": 14,
            "marker": "o",
            "zorder": 3,
        }
    if isinstance(agent, ThreatAgent):
        return {"color": "black", "size": 28, "marker": "X", "zorder": 4}
    if isinstance(agent, FoodSource):
        return {
            "color": "tab:green" if not agent.depleted else "saddlebrown",
            "size": 22,
            "marker": "s",
            "zorder": 1,
        }
    if isinstance(agent, HomePatch):
        return {"color": "steelblue", "size": 22, "marker": "H", "zorder": 1}
    return None


# ──────────────────────────────────────────────────────────────────────── #
#  Chart components                                                        #
# ──────────────────────────────────────────────────────────────────────── #

SpaceComponent = make_space_component(agent_portrayal)

NeedsChart = make_plot_component(
    {
        "MeanHunger": "tab:orange",
        "MeanRest": "tab:blue",
        "MeanSocial": "tab:green",
        "MeanSafety": "tab:red",
    },
    post_process=lambda ax: (
        ax.set_ylim(0, 1),
        ax.axhline(0.75, color="gray", linestyle="--", linewidth=0.7, alpha=0.6),
        ax.set_ylabel("Urgency (0=satisfied, 1=critical)"),
        ax.set_title("Mean Need Levels"),
    ),
)

ActiveNeedChart = make_plot_component(
    {
        "DrivenByHunger": "tab:orange",
        "DrivenByRest": "tab:blue",
        "DrivenBySocial": "tab:green",
        "DrivenBySafety": "tab:red",
    },
    post_process=lambda ax: (
        ax.set_ylabel("Agent count"),
        ax.set_title("Agents per Active Need"),
    ),
)

PreemptionChart = make_plot_component(
    {"CriticalAgents": "purple", "TotalPreemptions": "tab:red"},
    post_process=lambda ax: ax.set_title(
        "Critical Agents & Cumulative Preemptions (Pain Point #16)"
    ),
)

# ──────────────────────────────────────────────────────────────────────── #
#  Model parameters (interactive sliders)                                  #
# ──────────────────────────────────────────────────────────────────────── #

model_params = {
    "n_villagers": {
        "type": "SliderInt",
        "value": 20,
        "label": "Villagers",
        "min": 5,
        "max": 40,
        "step": 5,
    },
    "n_food": {
        "type": "SliderInt",
        "value": 8,
        "label": "Food patches",
        "min": 2,
        "max": 20,
        "step": 2,
    },
    "n_homes": {
        "type": "SliderInt",
        "value": 5,
        "label": "Home patches",
        "min": 1,
        "max": 15,
        "step": 1,
    },
    "n_threats": {
        "type": "SliderInt",
        "value": 2,
        "label": "Threats",
        "min": 0,
        "max": 6,
        "step": 1,
    },
    "width": {
        "type": "SliderInt",
        "value": 25,
        "label": "Grid width",
        "min": 15,
        "max": 40,
        "step": 5,
    },
    "height": {
        "type": "SliderInt",
        "value": 25,
        "label": "Grid height",
        "min": 15,
        "max": 40,
        "step": 5,
    },
}

# ──────────────────────────────────────────────────────────────────────── #
#  Solara app                                                              #
# ──────────────────────────────────────────────────────────────────────── #

page = SolaraViz(
    VillageModel,
    components=[SpaceComponent, NeedsChart, ActiveNeedChart, PreemptionChart],
    model_params=model_params,
    name="Needs-Based Village",
)
