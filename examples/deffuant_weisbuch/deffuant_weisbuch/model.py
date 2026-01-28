import statistics

from mesa import Model
from mesa.datacollection import DataCollector

from .agents import OpinionAgent


class DeffuantWeisbuchModel(Model):
    """Classical Deffuant-Weisbuch bounded confidence model.

    This model implements opinion dynamics in a well-mixed population.
    At each step, a random pair of agents is selected. If the difference
    between them is below a confidence threshold, both agents adjust their
    opinion toward each other.
    """

    def __init__(self, n=100, epsilon=0.2, mu=0.5, seed=None):
        """Initialize the model.

        Args:
            n (int): Number of agents in the population.
            epsilon (float): Confidence threshold for interaction.
            mu (float): Convergence rate controlling opinion adjustment.
            seed (int, optional): Random seed for reproducibility
        """
        super().__init__(seed=seed)

        self.n = n
        self.epsilon = epsilon
        self.mu = mu

        self.attempted_interactions = 0
        self.accepted_interactions = 0
        self.acceptance_rate = 0.0

        self.datacollector = DataCollector(
            model_reporters={
                "Variance": self.compute_variance,
                "Acceptance Rate": lambda m: m.acceptance_rate,
                "Cluster Count": self.compute_cluster_count,
            },
            agent_reporters={"opinion": "opinion"},  # type: ignore[attr-defined]
        )

        OpinionAgent.create_agents(
            model=self,
            n=self.n,
            opinion=[self.random.uniform(-1, 1) for _ in range(self.n)],
        )

        self.datacollector.collect(self)

    def step(self):
        """Execute one model step.

        A random pair of agents is selected. If their opinions differ by
        less than the confidence threshold, both agents update opinion values
        symmetrically.
        """
        agent_list = self.agents.to_list()
        for _ in range(self.n):
            agent_a, agent_b = self.random.sample(agent_list, 2)
            self.attempted_interactions += 1

            if abs(agent_a.opinion - agent_b.opinion) < self.epsilon:
                opinion_a = agent_a.opinion
                opinion_b = agent_b.opinion

                agent_a.update_opinion(opinion_b, self.mu)
                agent_b.update_opinion(opinion_a, self.mu)

                self.accepted_interactions += 1

        if self.attempted_interactions > 0:
            self.acceptance_rate = (
                self.accepted_interactions / self.attempted_interactions
            )

        else:
            self.acceptance_rate = 0.0

        self.datacollector.collect(self)

    def compute_variance(self):
        opinions = [agent.opinion for agent in self.agents]  # type: ignore[attr-defined]
        return statistics.variance(opinions) if opinions else 0

    def compute_cluster_count(self, delta: float = 0.01) -> int:
        opinions = sorted(agent.opinion for agent in self.agents)  # type: ignore[attr-defined]

        if not opinions:
            return 0

        cluster_count = 1

        for i in range(1, len(opinions)):
            if abs(opinions[i] - opinions[i - 1]) > delta:
                cluster_count += 1

        return cluster_count
