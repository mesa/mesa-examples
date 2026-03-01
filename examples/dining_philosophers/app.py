import matplotlib.ticker as ticker
import networkx as nx
import solara
from dining_philosophers.agent import ForkAgent, PhilosopherAgent, State
from dining_philosophers.model import DiningPhilosophersModel
from matplotlib.figure import Figure
from mesa.visualization import SolaraViz, make_plot_component
from mesa.visualization.utils import update_counter


@solara.component
def DiningTable(model):
    # This is required to trigger reactivity when the model steps
    update_counter.get()

    # Create a layout for the graph
    # We use circular layout.
    # The graph nodes are 0..2*N-1.
    # We want to scale these to SVG coordinates (0-100 or similar)

    # Re-calculate layout on every render or use the one from model if static
    # Since number of philosophers can change, we recalculate.
    # model.G is available.

    pos = nx.circular_layout(model.G)

    # SVG ViewBox: 0 0 400 400
    # Center: 200, 200. Radius: 150.

    svg_elements = []

    # Draw the table (circle)
    svg_elements.append(
        solara.v.Html(
            tag="circle",
            attributes={
                "cx": "200",
                "cy": "200",
                "r": "120",
                "fill": "#f5f5dc",
                "stroke": "#8b4513",
                "stroke-width": "5",
            },
        )
    )

    for agent in model.grid.agents:
        node_id = agent.cell.coordinate
        x, y = pos[node_id]

        # Map (-1, 1) to (50, 350)
        svg_x = 200 + x * 160
        svg_y = 200 + y * 160

        emoji = ""
        status_color = "gray"

        if isinstance(agent, PhilosopherAgent):
            if agent.state == State.THINKING:
                emoji = "🤔"
                status_color = "blue"
            elif agent.state == State.HUNGRY:
                emoji = "🤤"
                status_color = "red"
            elif agent.state == State.EATING:
                emoji = "🍝"
                status_color = "green"

            # Draw Philosopher
            svg_elements.append(
                solara.v.Html(
                    tag="text",
                    attributes={
                        "x": f"{svg_x}",
                        "y": f"{svg_y}",
                        "font-size": "40",
                        "text-anchor": "middle",
                        "dominant-baseline": "middle",
                    },
                    children=[emoji],
                )
            )
            # Draw Status Dot
            svg_elements.append(
                solara.v.Html(
                    tag="circle",
                    attributes={
                        "cx": f"{svg_x}",
                        "cy": f"{svg_y + 25}",
                        "r": "6",
                        "fill": status_color,
                        "stroke": "white",
                        "stroke-width": "1",
                    },
                )
            )

        elif isinstance(agent, ForkAgent):
            emoji = "🍴"
            # Fork color logic
            if agent.is_used:
                status_color = "red"  # Used
                opacity = "1.0"
            else:
                status_color = "green"  # Free
                opacity = "0.6"

            # Draw Fork
            # We place forks slightly closer to center or just on the ring
            # Since layout is circular alternating, they are already well placed.
            svg_elements.append(
                solara.v.Html(
                    tag="text",
                    attributes={
                        "x": f"{svg_x}",
                        "y": f"{svg_y}",
                        "font-size": "30",
                        "text-anchor": "middle",
                        "dominant-baseline": "middle",
                        "opacity": opacity,
                    },
                    children=[emoji],
                )
            )
            # Draw Status Dot for Fork
            svg_elements.append(
                solara.v.Html(
                    tag="circle",
                    attributes={
                        "cx": f"{svg_x}",
                        "cy": f"{svg_y + 20}",
                        "r": "4",
                        "fill": status_color,
                    },
                )
            )

    return solara.v.Html(
        tag="svg",
        attributes={"width": "400", "height": "400", "viewBox": "0 0 400 400"},
        children=svg_elements,
    )


@solara.component
def SpaghettiBarChart(model):
    update_counter.get()

    # Collect data from philosophers
    # We iterate through agents. Since it's a grid, we can just filter by type.
    # We want them sorted by ID (position)

    philosophers = []
    philosophers = sorted(
        model.agents_by_type[PhilosopherAgent], key=lambda p: p.position
    )

    labels = [f"P{p.position // 2}" for p in philosophers]
    values = [p.total_eaten for p in philosophers]

    fig = Figure()
    ax = fig.subplots()

    # Draw bar chart
    ax.bar(labels, values, color="orange", alpha=0.7, edgecolor="black")

    ax.set_title("Spaghetti Consumed per Philosopher")
    ax.set_ylabel("Bowls Eaten")
    ax.set_xlabel("Philosopher")

    # Set integer locator for y axis
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    solara.FigureMatplotlib(fig)


model_params = {
    "num_philosophers": {
        "type": "SliderInt",
        "value": 5,
        "label": "Number of Philosophers",
        "min": 3,
        "max": 10,
    },
    "hungry_chance": {
        "type": "SliderFloat",
        "value": 0.1,
        "label": "Hungry Chance",
        "min": 0.0,
        "max": 1.0,
        "step": 0.05,
    },
    "full_chance": {
        "type": "SliderFloat",
        "value": 0.2,
        "label": "Full Chance",
        "min": 0.0,
        "max": 1.0,
        "step": 0.05,
    },
    "strategy": {
        "type": "Select",
        "value": "Naive",
        "label": "Strategy",
        "values": ["Naive", "Atomic", "Cooperative"],
    },
}

StatePlot = make_plot_component(
    {"Thinking": "blue", "Hungry": "red", "Eating": "green"}
)

WaitTimePlot = make_plot_component({"Avg Wait Time": "orange"})


model = DiningPhilosophersModel()

page = SolaraViz(
    model,
    components=[
        DiningTable,  # Custom SVG visualization
        StatePlot,  # Line chart for states
        SpaghettiBarChart,  # Custom Bar Chart
        WaitTimePlot,
    ],
    model_params=model_params,
    name="Dining Philosophers",
)
