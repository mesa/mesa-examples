import solara
import matplotlib.pyplot as plt
from model import Trading_interface
from collections import defaultdict, Counter
import numpy as np
import threading
import time

# ==============================
# MODEL INIT
# ==============================

model = Trading_interface(300)

refresh = solara.reactive(0)
running = solara.reactive(False)


@solara.component
def Page():

    solara.Markdown("# 📈 Behavioral Stock Market Dashboard")

    # ==============================
    # AUTO RUN USING THREAD (SAFE)
    # ==============================

    def auto_loop():
        while running.value:
            model.step()
            refresh.value += 1
            time.sleep(0.5)

    def start_stop():
        if not running.value:
            running.value = True
            threading.Thread(target=auto_loop, daemon=True).start()
        else:
            running.value = False

    def step():
        model.step()
        refresh.value += 1

    def reset():
        global model
        running.value = False
        model = Trading_interface(300)
        refresh.value += 1

    # ==============================
    # CONTROLS
    # ==============================

    solara.Row([
        solara.Button("▶ STEP", on_click=step),
        solara.Button(
            "⏸ STOP" if running.value else "▶ AUTO RUN",
            on_click=start_stop
        ),
        solara.Button("🔄 RESET", on_click=reset),
    ])

    # Force re-render
    _ = refresh.value

    # ==============================
    # CURRENT PRICE
    # ==============================

    solara.Markdown(f"## 💰 Current Price: ₹ {model.share_price:.2f}")

    # ==============================
    # TRADER DISTRIBUTION
    # ==============================

    trader_types = [a.trader_type for a in model.agents]
    counts = Counter(trader_types)

    solara.Markdown("### 👥 Trader Distribution")
    for t, c in counts.items():
        solara.Markdown(f"- {t}: {c}")

    # ==============================
    # PROFIT + MIN/MAX ANALYSIS
    # ==============================

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

    # ==============================
    # GRAPH
    # ==============================

    data = model.datacollector.get_model_vars_dataframe()

    fig = plt.figure()
    plt.plot(data.index, data["Price"])
    plt.title("Price Over Time")
    plt.xlabel("Step")
    plt.ylabel("Price")

    solara.FigureMatplotlib(fig)