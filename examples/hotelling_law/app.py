import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import solara
from hotelling_law.agents import ConsumerAgent, StoreAgent
from hotelling_law.model import HotellingModel
from matplotlib.figure import Figure
from mesa.visualization import SolaraViz, make_plot_component

model_params = {
    "N_stores": {
        "type": "SliderInt",
        "value": 5,
        "label": "Number of stores:",
        "min": 2,
        "max": 10,
        "step": 1,
    },
    "N_consumers": {
        "type": "SliderInt",
        "value": 100,
        "label": "Number of Consumers:",
        "min": 50,
        "max": 200,
        "step": 10,
    },
    "mode": {
        "type": "Select",
        "value": "default",
        "label": "Mode:",
        "values": ["default", "pricing_only", "moving_only"],
    },
    "environment_type": {
        "type": "Select",
        "value": "grid",
        "label": "Environment Type:",
        "values": ["grid", "line"],
    },
    "mobility_rate": {
        "type": "SliderInt",
        "value": 100,
        "label": "Mobility Rate (%):",
        "min": 0,
        "max": 100,
        "step": 10,
    },
    "consumer_preferences": {
        "type": "Select",
        "value": "default",
        "label": "Consumer Preferences:",
        "values": ["default", "proximity", "price"],
    },
    "width": {
        "type": "SliderInt",
        "value": 20,  # Adjusted from 10 to 20 for wider grid
        "label": "Grid Width:",
        "min": 10,
        "max": 50,
        "step": 5,
    },
    "height": {
        "type": "SliderInt",
        "value": 20,  # Adjusted from 10 to 20 for taller grid
        "label": "Grid Height:",
        "min": 10,
        "max": 50,
        "step": 5,
    },
}

max_stores = model_params["N_stores"]["max"]

store_colors = plt.get_cmap("hsv", max_stores)


# This function defines how agents are visually represented in the simulation.
def agent_portrayal(agent):
    # Initialize default values
    size = 10  # Default size
    color = "grey"  # Default color for agents
    marker = "o"

    if isinstance(agent, StoreAgent):
        size = 60  # Larger size for visibility
        color = store_colors(agent.unique_id)
        marker = "d"

    elif isinstance(agent, ConsumerAgent):
        # ConsumerAgents are represented as smaller circles in grey
        size = 10
        if agent.preferred_store is None:
            color = "white"
        else:
            store_id = (
                agent.preferred_store.unique_id
                if isinstance(agent.preferred_store, StoreAgent)
                else agent.preferred_store
            )
            color = store_colors(store_id)

    # Construct and return the portrayal dictionary
    portrayal = {
        "size": size,
        "color": color,
        "marker": marker,
    }

    return portrayal


@solara.component
def SpaceDrawer(model):
    fig = Figure(figsize=(8, 5), dpi=100)
    ax = fig.subplots()

    # Set plot limits and aspect
    ax.set_xlim(0, model.grid.width)
    ax.set_ylim(0, model.grid.height)
    ax.set_aspect("equal")
    ax.invert_yaxis()  # Match grid's origin

    cell_store_contents = {}  # Track store agents in each cell
    jitter_amount = 0.3  # Jitter for visual separation

    for agent in model.agents:
        portrayal = agent_portrayal(agent)

        # Track store agents for cell coloring
        if isinstance(agent, StoreAgent):
            if agent.pos is None:
                continue
            if agent.pos not in cell_store_contents:
                cell_store_contents[agent.pos] = []
            cell_store_contents[agent.pos].append(portrayal)

    # Color cells based on store occupancy
    for pos, stores in cell_store_contents.items():
        num_stores = len(stores)
        width = 1 / num_stores  # Divide cell width by number of stores
        for i, store in enumerate(stores):
            # Calculate rectangle position and size for
            # each store's portion of the cell
            rect_x = pos[0] + (i * width)
            rect_y = pos[1]
            rect = patches.Rectangle(
                (rect_x, rect_y),
                width,
                1,
                linewidth=0.5,
                edgecolor="k",
                facecolor=store["color"],
            )
            ax.add_patch(rect)

    # Jittered scatter plot for all agents
    for agent in model.agents:
        if agent.pos is None:
            continue
        portrayal = agent_portrayal(agent)
        jitter_x = np.random.uniform(-jitter_amount, jitter_amount) + agent.pos[0] + 0.5
        jitter_y = np.random.uniform(-jitter_amount, jitter_amount) + agent.pos[1] + 0.5

        ax.scatter(
            jitter_x,
            jitter_y,
            color=portrayal.get("color", "black"),
            s=portrayal.get("size", 100),
            marker=portrayal.get("marker", "o"),
            linewidths=0.5,
            edgecolors="black",
            alpha=0.6,
        )

    fig.tight_layout()

    return solara.FigureMatplotlib(fig)


def make_market_share_and_price_chart(model):
    fig = Figure(figsize=(8, 5), dpi=100)
    ax = fig.subplots()

    # Get store agents and sort them by their unique_id
    # to ensure consistent order
    store_agents = [agent for agent in model.agents if isinstance(agent, StoreAgent)]
    store_agents_sorted = sorted(store_agents, key=lambda agent: agent.unique_id)

    # Now gather market shares, prices, and labels using the sorted list
    market_shares = [agent.market_share for agent in store_agents_sorted]
    prices = [agent.price for agent in store_agents_sorted]
    store_labels = [f"Store {agent.unique_id}" for agent in store_agents_sorted]
    colors = [agent_portrayal(agent)["color"] for agent in store_agents_sorted]

    # Calculate the number of groups and bar width
    n_groups = len(market_shares)
    bar_width = 0.35

    # Generate the positions for each group on the x-axis
    indices = np.arange(n_groups)

    # Define colors for market share and price bars
    market_share_color = "#1f77b4"  # Deep blue
    price_color = "#ff7f0e"  # Orange

    # Plot bars
    ax.bar(
        indices - bar_width / 2,
        market_shares,
        bar_width,
        label="Market Share",
        color=market_share_color,
        alpha=0.7,
    )
    ax.bar(
        indices + bar_width / 2,
        prices,
        bar_width,
        label="Price",
        color=price_color,
        alpha=0.7,
    )

    # Add labels, title, and legend
    ax.set_xticks(indices)
    ax.set_xticklabels(store_labels, rotation="vertical")
    for ticklabel, tickcolor in zip(ax.get_xticklabels(), colors):
        ticklabel.set_color(tickcolor)
    ax.set_title("Market Share and Price Distribution by Store")
    ax.set_xlabel("Stores")
    ax.set_ylabel("Value")
    ax.legend()

    fig.tight_layout()

    return solara.FigureMatplotlib(fig)


def make_price_changes_line_chart(model):
    fig = Figure(figsize=(8, 5), dpi=100)
    ax = fig.subplots()

    model_data = model.datacollector.get_model_vars_dataframe()

    # Retrieve agent colors based on their portrayal
    agent_colors = {
        f"Store_{agent.unique_id}_Price": agent_portrayal(agent)["color"]
        for agent in model.agents
        if isinstance(agent, StoreAgent)
    }

    for column in model_data.columns:
        if column.startswith("Store_") and column.endswith("_Price"):
            # Extract the store ID for labeling and determining the line color
            store_id = column.split("_")[1]
            line_color = agent_colors.get(column, "black")

            ax.plot(
                model_data.index,
                model_data[column],
                label=f"Store {store_id}",
                color=line_color,
            )

    ax.set_title("Price Changes of Each Store Over Time")
    ax.set_xlabel("Simulation Step")
    ax.set_ylabel("Price")
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1))

    fig.tight_layout()

    return solara.FigureMatplotlib(fig)


def make_market_share_line_chart(model):
    fig = Figure(figsize=(8, 5), dpi=100)
    ax = fig.subplots()

    model_data = model.datacollector.get_model_vars_dataframe()

    # Retrieve agent colors based on their portrayal
    agent_colors = {
        f"Store_{agent.unique_id}_Market Share": agent_portrayal(agent)["color"]
        for agent in model.agents
        if isinstance(agent, StoreAgent)
    }

    for column in model_data.columns:
        if column.startswith("Store_") and column.endswith("_Market Share"):
            # Extract the store ID for labeling and determining the line color
            store_id = column.split("_")[1]
            line_color = agent_colors.get(column, "black")

            ax.plot(
                model_data.index,
                model_data[column],
                label=f"Store {store_id}",
                color=line_color,
            )

    ax.set_title("Market share of Each Store Over Time")
    ax.set_xlabel("Simulation Step")
    ax.set_ylabel("Market Share")
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1))

    fig.tight_layout()

    return solara.FigureMatplotlib(fig)


def make_revenue_line_chart(model):
    fig = Figure(figsize=(8, 5), dpi=100)
    ax = fig.subplots()

    model_data = model.datacollector.get_model_vars_dataframe()

    # Retrieve agent colors based on their portrayal
    agent_colors = {
        f"Store_{agent.unique_id}_Revenue": agent_portrayal(agent)["color"]
        for agent in model.agents
        if isinstance(agent, StoreAgent)
    }

    for column in model_data.columns:
        if column.startswith("Store_") and column.endswith("_Revenue"):
            # Extract the store ID for labeling and determining the line color
            store_id = column.split("_")[1]
            line_color = agent_colors.get(column, "black")

            ax.plot(
                model_data.index,
                model_data[column],
                label=f"Store {store_id}",
                color=line_color,
            )

    ax.set_title("Revenue of Each Store Over Time")
    ax.set_xlabel("Simulation Step")
    ax.set_ylabel("Revenue")
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1))

    fig.tight_layout()

    return solara.FigureMatplotlib(fig)


model1 = HotellingModel(20, 20)

# Instantiate the SolaraViz component with your model
page = SolaraViz(
    model1,
    components=[
        SpaceDrawer,
        make_price_changes_line_chart,
        make_market_share_and_price_chart,
        make_market_share_line_chart,
        make_plot_component("Price Variance"),
        make_revenue_line_chart,
    ],
    name="Hotelling's Law Model",
    play_interval=150,
)

# Display the visualization in the Jupyter Notebook
page  # noqa
