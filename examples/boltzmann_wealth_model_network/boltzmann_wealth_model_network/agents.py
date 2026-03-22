from mesa.discrete_space import CellAgent


class MoneyAgent(CellAgent):
    """An agent with fixed initial wealth.

    Each agent starts with 1 unit of wealth and can give 1 unit to other agents
    if they occupy the same cell.

    Attributes:
        wealth (int): The agent's current wealth (starts at 1)
    """

    def __init__(self, model):
        """Create a new agent.

        Args:
            model (Model): The model instance that contains the agent
        """
        super().__init__(model)
        self.wealth = self.random.randint(1, self.model.max_wealth)

    def give_money(self):
        neighbors = [agent for agent in self.cell.neighborhood.agents if agent != self]
        if len(neighbors) > 0:
            other = self.random.choice(neighbors)
            other.wealth += 1
            self.wealth -= 1

    def step(self):
        empty_neighbors = [cell for cell in self.cell.neighborhood if cell.is_empty]
        if empty_neighbors:
            self.cell = self.random.choice(empty_neighbors)

        if self.wealth > 0:
            self.give_money()
