from mesa import Model
from mesa.discrete_space import CellAgent, OrthogonalMooreGrid


class WealthAgent(CellAgent):
    """An agent with fixed initial wealth."""

    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell
        self.wealth = 1

    def step(self):
        if self.wealth > 0:
            other_agent = self.model.random.choice(self.model.agents)
            if other_agent is not self:
                other_agent.wealth += 1
                self.wealth -= 1


class WealthModel(Model):
    """A simple model for wealth distribution."""

    def __init__(self, n=50, width=10, height=10, rng=None):
        super().__init__(rng=rng)
        self.num_agents = n
        self.grid = OrthogonalMooreGrid((width, height), torus=True, random=self.random)

        all_cells = self.grid.all_cells.cells
        placement_cells = self.random.sample(all_cells, k=self.num_agents)

        for cell in placement_cells:
            WealthAgent(self, cell)

    def get_gini(self):
        """Calculate the Gini coefficient of wealth distribution."""
        agent_wealths = [agent.wealth for agent in self.agents]
        x = sorted(agent_wealths)
        n = self.num_agents
        if n == 0 or sum(x) == 0:
            return 0
        b = sum(xi * (n - i) for i, xi in enumerate(x)) / (n * sum(x))
        return 1 + (1 / n) - 2 * b

    def step(self):
        self.agents.shuffle_do("step")
