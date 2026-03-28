import matplotlib.pyplot as plt
import mesa
import seaborn as sns


class MoneyAgent(mesa.Agent):
    """An agent with fixed initial wealth."""

    def __init__(self, model):
        super().__init__(model)
        self.wealth = 1

    def exchange(self):
        if self.wealth > 0:
            other_agent = self.random.choice(self.model.agents)
            if other_agent is not None:
                other_agent.wealth += 1
                self.wealth -= 1


class MoneyModel(mesa.Model):
    """A model with some number of agents."""

    def __init__(self, n=10, seed=None):
        super().__init__(seed=seed)
        self.num_agents = n
        MoneyAgent.create_agents(model=self, n=n)

    def step(self):
        self.agents.shuffle_do("exchange")


if __name__ == "__main__":
    model = MoneyModel(10)
    for _ in range(30):
        model.step()

    agent_wealth = [a.wealth for a in model.agents]
    g = sns.histplot(agent_wealth, discrete=True)
    g.set(title="Wealth distribution", xlabel="Wealth", ylabel="number of agents")
    plt.show()
