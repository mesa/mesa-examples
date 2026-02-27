import solara
import matplotlib.pyplot as plt
import solara.lab
from mesa.visualization import SolaraViz, make_plot_component
from information_cascades.model import TradingDWModel



def TradingPerformanceStats(model):
    agents = list(model.agents)
    if not agents: return solara.Text("initializing...")

    avg_gross = sum(a.gross_wealth for a in agents) / len(agents)
    avg_net = sum(a.net_wealth for a in agents) / len(agents)

    sorted_agents = sorted(agents, key=lambda x: x.trades)
    n = len(sorted_agents)
    split = max(1, n // 5)

    low_traders = sorted_agents[:split]
    high_traders = sorted_agents[-split:]

    avg_net_low = sum(a.net_wealth for a in low_traders) / len(low_traders)
    avg_net_high = sum(a.net_wealth for a in high_traders) / len(high_traders)


    return solara.Card(
        title="Barber & Odean (2000) Validation",
        children=[
            solara.Markdown(f"**Market Avg (Gross)**: {avg_gross:.2f}"),
            solara.Markdown(f"**Market Avg (Net)**: {avg_net:.2f}"),
            solara.Markdown("---"),
            solara.Markdown(
                f"**Low Turnover Top 20% Net Wealth**: <span style='color:green; font-weight:bold;'>{avg_net_low:.2f}</span>"),
            solara.Markdown(
                f"**High Turnover Top 20% Net Wealth**: <span style='color:red; font-weight:bold;'>{avg_net_high:.2f}</span>"),
        ]
    )


def WealthVsConfidenceScatter(model):
    fig, ax = plt.subplots(figsize=(6, 4), constrained_layout=True)
    agents = list(model.agents)
    confidences = [a.confidence for a in agents]
    wealths = [a.net_wealth for a in agents]

    if wealths:
        avg_w = sum(wealths) / len(wealths)
        sc = ax.scatter(confidences, wealths, alpha=0.6, c=wealths, cmap="RdYlGn")

        w_min, w_max = min(wealths), max(wealths)
        padding = (w_max - w_min) * 0.2 if w_max > w_min else 10
        ax.set_ylim(w_min - padding, w_max + padding)

        ax.axhline(avg_w, color='blue', linestyle='--', alpha=0.5)
        ax.fill_between([1, 5], w_min - padding, avg_w, color='red', alpha=0.1, label='Underperforming')

        ax.set_xlabel("Confidence Level")
        ax.set_ylabel("Net Wealth")
        ax.set_title("Trading is Hazardous to Your Wealth")

    return solara.FigureMatplotlib(fig)


def OpinionTrajectoryPlot(model):
    fig, ax = plt.subplots(figsize=(6, 4), constrained_layout=True)
    df = model.datacollector.get_agent_vars_dataframe()
    if df.empty:
        return solara.FigureMatplotlib(fig)

    opinions = df["opinion"].unstack()
    opinions.plot(ax=ax, legend=False, alpha=0.4)
    ax.set_xlabel("Steps")
    ax.set_ylabel("Opinion")
    ax.set_title("Herd Formation (Banerjee, 1992)")
    return solara.FigureMatplotlib(fig)


model_params = {
    "n": {
        "type": "SliderInt",
        "value": 100,
        "label": "Number of Investors",
        "min": 20,
        "max": 300,
        "step": 1
    },
    "epsilon": {
        "type": "SliderFloat",
        "value": 0.6,
        "label": "Confidence Threshold (ε)",
        "min": 0.01,
        "max": 1.0,
        "step": 0.01
    },
    "mu": {
        "type": "SliderFloat",
        "value": 0.1,
        "label": "Convergence Rate (μ)",
        "min": 0.01,
        "max": 0.5,
        "step": 0.01
    },
    "transaction_cost": {
        "type": "SliderFloat",
        "value": 0.5,
        "label": "Transaction Cost",
        "min": 0,
        "max": 10,
        "step": 0.5
    },
}

initial_model = TradingDWModel()

page = SolaraViz(
    model=initial_model,
    model_params=model_params,
    components=[
        TradingPerformanceStats,
        OpinionTrajectoryPlot,
        WealthVsConfidenceScatter,
        make_plot_component("Variance"),
        make_plot_component(["Avg Gross Wealth", "Avg Net Wealth"]),
    ]
)