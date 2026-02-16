import networkx as nx
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.discrete_space import Network

from .agents import MoneyAgent


class BoltzmannWealthModelNetwork(Model):
    """A model with some number of agents."""

    def __init__(self, n=7, num_nodes=10, rng=None):
        super().__init__(rng=rng)

        self.num_agents = n
        self.num_nodes = num_nodes if num_nodes >= self.num_agents else self.num_agents
        self.G = nx.erdos_renyi_graph(n=self.num_nodes, p=0.5)
        self.grid = Network(self.G, capacity=1, random=self.random)

        # Set up data collection
        self.datacollector = DataCollector(
            model_reporters={"Gini": self.compute_gini},
            agent_reporters={"Wealth": "wealth"},
        )

        # Create agents; add the agent to a random node
        # TODO: change to MoneyAgent.create_agents(...)
        list_of_random_nodes = self.random.sample(list(self.G), self.num_agents)
        for position in list_of_random_nodes:
            agent = MoneyAgent(self)
            agent.move_to(self.grid[position])

        self.running = True
        self.datacollector.collect(self)

    def step(self):
        self.agents.shuffle_do("step")  # Activate all agents in random order
        self.datacollector.collect(self)  # collect data

    def compute_gini(self):
        agent_wealths = [agent.wealth for agent in self.agents]
        x = sorted(agent_wealths)
        num_agents = self.num_agents
        B = sum(xi * (num_agents - i) for i, xi in enumerate(x)) / (num_agents * sum(x))  # noqa: N806
        return 1 + (1 / num_agents) - 2 * B
