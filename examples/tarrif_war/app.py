import matplotlib
import matplotlib.style
import solara
from matplotlib.figure import Figure
from mesa.visualization import SolaraViz
from mesa.visualization.utils import update_counter
from tarrif_war.model import TariffWarModel

matplotlib.use("Agg")
matplotlib.style.use("seaborn-v0_8-whitegrid")

# ── Colour palette ─────────────────────────────────────────────────────────────
COLORS = {
    "USA": "#4472C4",
    "China": "#C00000",
    "Neutral Asia": "#70AD47",
}
SECTOR_COLORS = {
    "Tech": "#9B59B6",
    "Agriculture": "#27AE60",
    "Manufacturing": "#E67E22",
}


# ── Chart 1: β Evolution & Lobbying (CEE-SAC recession spiral) ────────────────
@solara.component
def BetaLobbyingPlot(model):
    """
    β < 0  → firms systematically expect FALLING demand (self-fulfilling spiral).
    Lobbying power (right axis) shows how tariff rents get converted into political
    influence that LOCKS IN high tariffs after the crisis.
    """
    update_counter.get()
    fig = Figure(figsize=(5, 4))
    ax1 = fig.subplots()
    ax2 = ax1.twinx()

    df = model.datacollector.get_model_vars_dataframe()
    if len(df) >= 2:
        ax1.plot(df.index, df["Beta_USA"], color=COLORS["USA"], lw=2, label="β USA")
        ax1.plot(
            df.index, df["Beta_China"], color=COLORS["China"], lw=2, label="β China"
        )
        ax1.plot(
            df.index,
            df["Beta_Neutral"],
            color=COLORS["Neutral Asia"],
            lw=1.5,
            linestyle="--",
            label="β Neutral Asia",
        )
        ax1.axhline(0, color="black", lw=1.0, linestyle=":", label="β = 0")
        ax1.set_ylabel("β  (< 0 = firms expect decline)", fontsize=8)
        ax1.set_ylim(-1.05, 1.05)

        ax2.fill_between(df.index, df["Lobby_USA"], alpha=0.18, color=COLORS["USA"])
        ax2.fill_between(df.index, df["Lobby_China"], alpha=0.18, color=COLORS["China"])
        ax2.plot(
            df.index,
            df["Lobby_USA"],
            color=COLORS["USA"],
            lw=1.0,
            alpha=0.6,
            linestyle="-.",
        )
        ax2.plot(
            df.index,
            df["Lobby_China"],
            color=COLORS["China"],
            lw=1.0,
            alpha=0.6,
            linestyle="-.",
        )
        ax2.set_ylabel("Avg Lobbying Power  →", fontsize=7, color="gray")
        ax2.tick_params(axis="y", labelcolor="gray", labelsize=7)

    lines, labels = ax1.get_legend_handles_labels()
    ax1.legend(lines, labels, fontsize=7, loc="lower left")
    ax1.set_title(
        "Firm Pessimism (β) & Lobbying Buildup", fontsize=9, fontweight="bold"
    )
    ax1.set_xlabel("Step")
    fig.tight_layout()
    solara.FigureMatplotlib(fig)


# ── Chart 2: Expected Demand vs Actual Production ─────────────────────────────
@solara.component
def ExpectationProductionPlot(model):
    """Gap = forecast error. Widening gap → recession spiral in motion."""
    update_counter.get()
    fig = Figure(figsize=(5, 3.8))
    ax = fig.subplots()
    df = model.datacollector.get_model_vars_dataframe()

    if len(df) >= 2:
        ax.plot(
            df.index,
            df["Global_Expected_Demand"],
            color="#4472C4",
            lw=2,
            label="Expected Demand",
        )
        ax.plot(
            df.index,
            df["Global_Actual_Production"],
            color="#ED7D31",
            lw=2,
            label="Actual Production",
            linestyle="--",
        )
        ax.fill_between(
            df.index,
            df["Global_Expected_Demand"],
            df["Global_Actual_Production"],
            alpha=0.12,
            color="#7030A0",
            label="Forecast Gap",
        )
        ax.legend(fontsize=8)

    ax.set_title("Expected Demand vs Actual Production", fontsize=9, fontweight="bold")
    ax.set_xlabel("Step")
    ax.set_ylabel("Avg per-firm units")
    fig.tight_layout()
    solara.FigureMatplotlib(fig)


# ── Chart 3: Bilateral Tariffs (Ratchet Effect) ───────────────────────────────
@solara.component
def TariffPlot(model):
    update_counter.get()
    fig = Figure(figsize=(5, 3.8))
    ax = fig.subplots()
    df = model.datacollector.get_model_vars_dataframe()

    if len(df) >= 2:
        ax.plot(
            df.index,
            df["USA_China_Tariff"] * 100,
            color=COLORS["USA"],
            lw=2,
            label="USA → China",
        )
        ax.plot(
            df.index,
            df["China_USA_Tariff"] * 100,
            color=COLORS["China"],
            lw=2,
            label="China → USA",
        )
        ax.axhline(y=3, color="gray", lw=0.8, linestyle=":", label="WTO baseline 3%")
        ax.axhline(
            y=25,
            color="orange",
            lw=0.9,
            linestyle="--",
            alpha=0.6,
            label="2018-19 peak 25%",
        )
        ax.axhline(
            y=35,
            color="black",
            lw=0.7,
            linestyle="--",
            alpha=0.4,
            label="Model cap 35%",
        )
        ax.set_ylim(0, 40)
        ax.set_ylabel("Tariff Rate (%)")
        ax.legend(fontsize=8)

    ax.set_title(
        "Bilateral Tariffs - Ratchet & Back-and-Forth", fontsize=9, fontweight="bold"
    )
    ax.set_xlabel("Step")
    fig.tight_layout()
    solara.FigureMatplotlib(fig)


# ── Chart 4: Average Government Size (Ratchet Effect) ─────────────────────────
@solara.component
def GovSizePlot(model):
    update_counter.get()
    fig = Figure(figsize=(5, 3.8))
    ax = fig.subplots()
    df = model.datacollector.get_model_vars_dataframe()

    if len(df) >= 2:
        ax.plot(
            df.index, df["Avg_Gov_Size"], color="#7030A0", lw=2.5, label="Avg Gov Size"
        )
        ax.axhline(
            y=20.0,
            color="gray",
            lw=0.9,
            linestyle=":",
            label="Peacetime baseline (20% GDP)",
        )
        ax.set_ylabel("Gov Size (% of GDP)")
        ax.legend(fontsize=8)

    ax.set_title(
        "Average Government Size - Step-wise Ratchet", fontsize=9, fontweight="bold"
    )
    ax.set_xlabel("Step")
    fig.tight_layout()
    solara.FigureMatplotlib(fig)


# ── Chart 5: Country GDP & Trade Balance ──────────────────────────────────────
@solara.component
def GDPPlot(model):
    """GDP lines (left) + trade balance shading (right)."""
    update_counter.get()
    fig = Figure(figsize=(5, 3.8))
    ax1 = fig.subplots()
    ax2 = ax1.twinx()
    df = model.datacollector.get_model_vars_dataframe()

    if len(df) >= 2:
        ax1.plot(df.index, df["USA_GDP"], color=COLORS["USA"], lw=2, label="USA GDP")
        ax1.plot(
            df.index, df["China_GDP"], color=COLORS["China"], lw=2, label="China GDP"
        )
        ax1.plot(
            df.index,
            df["NeutralAsia_GDP"],
            color=COLORS["Neutral Asia"],
            lw=2,
            label="Neutral Asia GDP",
        )
        ax1.set_ylabel("Total Production (GDP proxy)")

        ax2.fill_between(
            df.index, df["TradeBalance_USA"], alpha=0.15, color=COLORS["USA"]
        )
        ax2.fill_between(
            df.index,
            df["TradeBalance_Neutral"],
            alpha=0.15,
            color=COLORS["Neutral Asia"],
        )
        ax2.axhline(0, color="black", lw=0.7, linestyle=":")
        ax2.set_ylabel("Trade Balance  →", fontsize=7, color="gray")
        ax2.tick_params(axis="y", labelcolor="gray", labelsize=7)

        lines, labels = ax1.get_legend_handles_labels()
        ax1.legend(lines, labels, fontsize=8)

    ax1.set_title("Country GDP & Trade Balance (shaded)", fontsize=9, fontweight="bold")
    ax1.set_xlabel("Step")
    fig.tight_layout()
    solara.FigureMatplotlib(fig)


# ── Chart 6: Firm Health (Bankruptcy Rate + Avg Profit) ───────────────────────
@solara.component
def FirmHealthPlot(model):
    """
    Bankruptcy rate (left, %) reveals which country's firms suffer most.
    Average profit (right) shows when firms tip from gain to sustained loss.
    """
    update_counter.get()
    fig = Figure(figsize=(9, 5))
    ax1 = fig.subplots()
    ax2 = ax1.twinx()
    df = model.datacollector.get_model_vars_dataframe()

    if len(df) >= 2:
        ax1.plot(
            df.index,
            df["Bankruptcy_USA"] * 100,
            color=COLORS["USA"],
            lw=2.5,
            label="USA bankruptcy %",
        )
        ax1.plot(
            df.index,
            df["Bankruptcy_China"] * 100,
            color=COLORS["China"],
            lw=2.5,
            label="China bankruptcy %",
        )
        ax1.plot(
            df.index,
            df["Bankruptcy_Neutral"] * 100,
            color=COLORS["Neutral Asia"],
            lw=2,
            linestyle="--",
            label="Neutral bankruptcy %",
        )
        ax1.set_ylabel("Firm Bankruptcy Rate (%)", fontsize=10)
        ax1.set_ylim(0, 105)

        ax2.plot(
            df.index,
            df["AvgProfit_USA"],
            color=COLORS["USA"],
            lw=1.5,
            alpha=0.6,
            linestyle="-.",
        )
        ax2.plot(
            df.index,
            df["AvgProfit_China"],
            color=COLORS["China"],
            lw=1.5,
            alpha=0.6,
            linestyle="-.",
        )
        ax2.plot(
            df.index,
            df["AvgProfit_Neutral"],
            color=COLORS["Neutral Asia"],
            lw=1.5,
            alpha=0.6,
            linestyle="-.",
        )
        ax2.axhline(0, color="black", lw=0.8, linestyle=":")
        ax2.set_ylabel("Avg Firm Profit  →", fontsize=9, color="gray")
        ax2.tick_params(axis="y", labelcolor="gray", labelsize=9)

        lines, labels = ax1.get_legend_handles_labels()
        ax1.legend(lines, labels, fontsize=9, loc="upper left")

    ax1.set_title(
        "Firm Health: Bankruptcy Rate & Avg Profit", fontsize=11, fontweight="bold"
    )
    ax1.set_xlabel("Step", fontsize=10)
    fig.tight_layout()
    solara.FigureMatplotlib(fig)


# ── Chart 7: Consumer Welfare ─────────────────────────────────────────────────
@solara.component
def WelfarePlot(model):
    """
    Consumer welfare composite (consumption x tariff-price burden x unemployment).
    Neutral Asia residents should fare better; USA/China consumers suffer most.
    """
    update_counter.get()
    fig = Figure(figsize=(5, 3.8))
    ax = fig.subplots()
    df = model.datacollector.get_model_vars_dataframe()

    if len(df) >= 2:
        ax.plot(df.index, df["Welfare_USA"], color=COLORS["USA"], lw=2, label="USA")
        ax.plot(
            df.index, df["Welfare_China"], color=COLORS["China"], lw=2, label="China"
        )
        ax.plot(
            df.index,
            df["Welfare_Neutral"],
            color=COLORS["Neutral Asia"],
            lw=2,
            label="Neutral Asia",
        )
        ax.fill_between(df.index, df["Welfare_USA"], alpha=0.07, color=COLORS["USA"])
        ax.fill_between(
            df.index, df["Welfare_Neutral"], alpha=0.07, color=COLORS["Neutral Asia"]
        )
        ax.set_ylabel("Consumer Welfare Index")
        ax.legend(fontsize=8)

    ax.set_title(
        "Consumer Welfare - Who Pays for the Trade War?", fontsize=9, fontweight="bold"
    )
    ax.set_xlabel("Step")
    fig.tight_layout()
    solara.FigureMatplotlib(fig)


# ── Model parameters ───────────────────────────────────────────────────────────
model_params = {
    "global_crisis": {
        "type": "Checkbox",
        "value": True,
        "label": "Trigger Tariff Shock (Global Crisis)",
    },
    "base_global_demand": {
        "type": "SliderInt",
        "value": 100,
        "min": 50,
        "max": 300,
        "step": 10,
        "label": "Base Global Demand",
    },
    "retaliation_intensity": {
        "type": "SliderFloat",
        "value": 0.08,
        "min": 0.01,
        "max": 0.20,
        "step": 0.01,
        "label": "Retaliation Intensity (per round)",
    },
    "lobbying_sensitivity": {
        "type": "SliderFloat",
        "value": 0.25,
        "min": 0.00,
        "max": 0.80,
        "step": 0.05,
        "label": "Lobbying Sensitivity",
    },
    "expectation_adaptation_rate": {
        "type": "SliderFloat",
        "value": 0.15,
        "min": 0.01,
        "max": 0.40,
        "step": 0.01,
        "label": "Expectation Adaptation Rate (β speed)",
    },
    "production_elasticity": {
        "type": "SliderFloat",
        "value": 0.40,
        "min": 0.10,
        "max": 0.80,
        "step": 0.05,
        "label": "Production Elasticity",
    },
    "trade_stickiness": {
        "type": "SliderFloat",
        "value": 0.40,
        "min": 0.00,
        "max": 0.90,
        "step": 0.05,
        "label": "Trade Stickiness",
    },
    "n_firms_per_country": {
        "type": "SliderInt",
        "value": 6,
        "min": 3,
        "max": 20,
        "step": 1,
        "label": "Firms per Country",
    },
    "seed": 42,
}

# ── Launch ─────────────────────────────────────────────────────────────────────
model = TariffWarModel()

page = SolaraViz(
    model,
    components=[
        BetaLobbyingPlot,
        ExpectationProductionPlot,
        TariffPlot,
        GovSizePlot,
        GDPPlot,
        FirmHealthPlot,
        WelfarePlot,
    ],
    model_params=model_params,
    name="Tariff War: Ratchet Effect & Trade Diversion",
)
page  # noqa: B018
