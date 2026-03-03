import threading
import time
from collections import Counter, defaultdict

import matplotlib.pyplot as plt
import numpy as np
import solara
from model import TradingInterface

# ==========================================================
# APPLICATION STATE (Avoid using global variables)
# ==========================================================

state = {"model": TradingInterface(300)}

refresh = solara.reactive(0)
running = solara.reactive(False)


@solara.component
def Page():
    solara.Markdown("# 📈 Behavioral Stock Market Dashboard")

    model = state["model"]

    # ==========================================================
    # AUTO-RUN LOOP (Runs simulation safely in background thread)
    # ==========================================================

    def auto_loop():
        while running.value:
            model.step()
            refresh.value += 1
            time.sleep(0.5)

    def start_stop():
        """Toggle automatic simulation."""
        if not running.value:
            running.value = True
            threading.Thread(target=auto_loop, daemon=True).start()
        else:
            running.value = False

    def step():
        """Execute a single simulation step."""
        model.step()
        refresh.value += 1

    def reset():
        """Reset the simulation to initial state."""
        running.value = False
        state["model"] = TradingInterface(300)
        refresh.value += 1

    # ==========================================================
    # CONTROL BUTTONS
    # ==========================================================

    solara.Row(
        [
            solara.Button("▶ STEP", on_click=step),
            solara.Button(
                "⏸ STOP" if running.value else "▶ AUTO RUN", on_click=start_stop
            ),
            solara.Button("🔄 RESET", on_click=reset),
        ]
    )

    # Force re-render
    _ = refresh.value

    # ==========================================================
    # CURRENT MARKET PRICE
    # ==========================================================

    solara.Markdown(f"## 💰 Current Price: ₹ {model.share_price:.2f}")

    # ==========================================================
    # TRADER DISTRIBUTION
    # ==========================================================

    trader_types = [agent.trader_type for agent in model.agents]
    counts = Counter(trader_types)

    solara.Markdown("### 👥 Trader Distribution")
    for trader_type, count in counts.items():
        solara.Markdown(f"- {trader_type}: {count}")

    # ==========================================================
    # GROUP WEALTH ANALYSIS
    # ==========================================================

    group_wealth = defaultdict(list)

    for agent in model.agents:
        wealth = agent.amount + agent.volume * model.share_price
        group_wealth[agent.trader_type].append(wealth)

    if group_wealth:
        solara.Markdown("### 🏆 Group Performance Analysis")

        avg_dict = {}

        for group, values in group_wealth.items():
            avg = np.mean(values)
            highest = np.max(values)
            lowest = np.min(values)

            avg_dict[group] = avg

            solara.Markdown(f"#### {group}")
            solara.Markdown(f"- Avg Wealth: ₹ {avg:,.2f}")
            solara.Markdown(f"- Highest Wealth: ₹ {highest:,.2f}")
            solara.Markdown(f"- Lowest Wealth: ₹ {lowest:,.2f}")

        best_group = max(avg_dict, key=avg_dict.get)
        solara.Markdown(f"## 🚀 Best Performing Strategy: **{best_group}**")

    # ==========================================================
    # PRICE TIME SERIES GRAPH
    # ==========================================================

    data = model.datacollector.get_model_vars_dataframe()

    fig = plt.figure()
    plt.plot(data.index, data["Price"])
    plt.title("Price Over Time")
    plt.xlabel("Step")
    plt.ylabel("Price")

    solara.FigureMatplotlib(fig)
