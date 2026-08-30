import networkx as nx
import numpy as np
from mesa import DataCollector, Model
from mesa.experimental.cell_space import Network

from .agents import NodeAgent


def calculate_nodes_with_degree_1(model):
    _, degree = zip(*model.graph.degree())
    return sum(1 for deg in degree if deg == 1)


class AgentNetwork(Model):
    def __init__(self, num=30, seed=42):
        """Initialize the model.

        Args:
            num: Number of Node Agents,
            seed : Random seed for reproducibility.
        """
        super().__init__(seed=seed)
        self.num = num
        self.random = seed
        self.curr_node = 1
        self.graph = nx.Graph()

        # Adding nodes to the graph
        for i in range(self.num):
            self.graph.add_node(i)

        self.graph.add_edge(0, 1)

        self.datacollector = DataCollector(
            {
                "Degree": calculate_nodes_with_degree_1,
            }
        )

        self.grid = Network(self.graph, capacity=1, random=self.random)
        NodeAgent.create_agents(model=self, n=self.num, cell=list(self.grid.all_cells))

    def step(self):
        self.curr_node += 1

        nodes, degree = zip(*self.graph.degree())
        total_degree = sum(degree)

        # probabilities of connecting to an existing node
        probabilities = [d / total_degree for d in degree]

        # choose an existing node based on the computed probabilities
        chosen_node = np.random.choice(nodes, p=probabilities)

        # add the new node and connect it to the choosen node
        self.graph.add_edge(chosen_node, self.curr_node)

        self.datacollector.collect(self)
        if self.steps >= self.num - 2:
            self.running = False
