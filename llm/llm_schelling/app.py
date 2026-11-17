import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

import matplotlib.pyplot as plt  # noqa: E402
import solara  # noqa: E402
from llm_schelling.model import LLMSchellingModel  # noqa: E402
from mesa.visualization import SolaraViz  # noqa: E402
from mesa.visualization.utils import update_counter  # noqa: E402

GROUP_COLORS = {0: "#2196F3", 1: "#FF5722"}  # Blue, Orange

model_params = {
    "width": {
        "type": "SliderInt",
        "value": 5,
        "label": "Grid width",
        "min": 5,
        "max": 20,
        "step": 1,
    },
    "height": {
        "type": "SliderInt",
        "value": 5,
        "label": "Grid height",
        "min": 5,
        "max": 20,
        "step": 1,
    },
    "density": {
        "type": "SliderFloat",
        "value": 0.8,
        "label": "Population density",
        "min": 0.1,
        "max": 1.0,
        "step": 0.05,
    },
    "minority_fraction": {
        "type": "SliderFloat",
        "value": 0.4,
        "label": "Minority fraction",
        "min": 0.1,
        "max": 0.5,
        "step": 0.05,
    },
}


def SchellingGridPlot(model):
    """Visualize the grid showing agent groups and happiness."""
    update_counter.get()

    width = model.grid.dimensions[0]
    height = model.grid.dimensions[1]

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Schelling Segregation (LLM)\nBlue=Group A, Orange=Group B, X=Unhappy")

    for agent in model.agents:
        x, y = agent.pos
        color = GROUP_COLORS[agent.group]
        marker = "o" if agent.is_happy else "x"
        ax.plot(
            x + 0.5,
            y + 0.5,
            marker=marker,
            color=color,
            markersize=8,
            markeredgewidth=2,
        )

    return solara.FigureMatplotlib(fig)


def SchellingStatsPlot(model):
    """Combined happiness + segregation index chart."""
    update_counter.get()

    df = model.datacollector.get_model_vars_dataframe()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 5), facecolor="#1a1a2e")
    fig.patch.set_facecolor("#1a1a2e")

    for ax in (ax1, ax2):
        ax.set_facecolor("#16213e")
        ax.tick_params(colors="white")
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        ax.title.set_color("white")
        for spine in ax.spines.values():
            spine.set_edgecolor("#444")

    if not df.empty:
        ax1.plot(df.index, df["happy"], color="#4CAF50", label="Happy", linewidth=2)
        ax1.plot(df.index, df["unhappy"], color="#F44336", label="Unhappy", linewidth=2)
    ax1.set_title("Agent Happiness", fontsize=11)
    ax1.set_ylabel("Count", color="white")
    ax1.legend(facecolor="#16213e", labelcolor="white", fontsize=8)

    if not df.empty and "segregation_index" in df.columns:
        ax2.plot(df.index, df["segregation_index"], color="#2196F3", linewidth=2)
    ax2.set_title("Segregation Index", fontsize=11)
    ax2.set_ylabel("Index", color="white")
    ax2.set_xlabel("Step", color="white")

    fig.tight_layout(pad=1.5)
    return solara.FigureMatplotlib(fig)


model = LLMSchellingModel()

page = SolaraViz(
    model,
    components=[
        SchellingGridPlot,
        SchellingStatsPlot,
    ],
    model_params=model_params,
    name="LLM Schelling Segregation",
)
