import random

from mesa import Model

from .agents import DecisionAgent


class DecisionModel(Model):
    """
    Demonstrates agent-level interruptions (arrest → release)
    using step-based timing compatible with Mesa 3.4.x.
    """

    def __init__(self, n_agents: int = 5):
        super().__init__()

        self.my_agents = [DecisionAgent(self) for _ in range(n_agents)]

        self.next_arrest_time = 3

    def arrest_someone(self):
        """Randomly arrest one free agent."""
        free_agents = [a for a in self.my_agents if a.status == "FREE"]
        if not free_agents:
            return

        agent = random.choice(free_agents)
        agent.get_arrested(sentence=4, current_time=self.time)

    def step(self):
        """
        Advance the model by one step.
        """

        if self.time == self.next_arrest_time:
            self.arrest_someone()
            self.next_arrest_time += 6

        for agent in self.my_agents:
            agent.step(self.time)
