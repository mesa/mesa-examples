"""Configure visualization elements and instantiate a server"""

import networkx as nx
import solara
import os
from aco_tsp.model import AcoTspModel, TSPGraph
from matplotlib.figure import Figure
from mesa.visualization import SolaraViz, make_plot_component


def circle_portrayal_example(agent):
    return {"node_size": 20, "width": 0.1}

tsp_graph = TSPGraph.from_tsp_file(os.path.join(os.path.dirname(__file__), "aco_tsp/data/kroA100.tsp"))
model_params = {
    "num_agents": tsp_graph.num_cities,
    "tsp_graph": tsp_graph,
    "ant_alpha": {
        "type": "SliderFloat",
        "value": 1.0,
        "label": "Alpha: pheromone exponent",
        "min": 0.0,
        "max": 10.0,
        "step": 0.1,
    },
    "ant_beta": {
        "type": "SliderFloat",
        "value": 5.0,
        "label": "Beta: heuristic exponent",
        "min": 0.0,
        "max": 10.0,
        "step": 0.1,
    },
}

model = AcoTspModel()


def make_graph(model):
    fig = Figure()
    ax = fig.subplots()
    ax.set_title("Cities and pheromone trails")
    graph = model.grid.G
    pos = model.tsp_graph.pos
    weights = [graph[u][v]["pheromone"] for u, v in graph.edges()]
    # normalize the weights
    weights = [w / max(weights) for w in weights]

    nx.draw(
        graph,
        ax=ax,
        pos=pos,
        node_size=10,
        width=weights,
        edge_color="gray",
    )

    return solara.FigureMatplotlib(fig)


def ant_level_distances(model):
    # ant_distances = model.datacollector.get_agent_vars_dataframe()
    # Plot so that the step index is the x-axis, there's a line for each agent,
    # and the y-axis is the distance traveled
    # ant_distances['tsp_distance'].unstack(level=1).plot(ax=ax)
    pass


page = SolaraViz(
    model,
    components=[
        make_plot_component(["best_distance_iter", "best_distance"]),
        make_graph,
    ],
    model_params=model_params,
    play_interval=1,
)
