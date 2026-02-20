from mesa import Model
from mesa.datacollection import DataCollector

from .agent import GamblingAgent


class LuckVsSkillModel(Model):
    def __init__(
        self,
        num_agents=200,
        alpha=0.05,
        initial_wealth=100,
        bet_size=1,
        seed=None,
    ):
        super().__init__(seed=seed)

        self.alpha = alpha
        self.steps = 0

        # Create agents
        for _ in range(num_agents):
            agent = GamblingAgent(
                model=self,
                skill=self.random.random(),
                wealth=initial_wealth,
                bet_size=bet_size,
            )
            self.agents.add(agent)

        self.datacollector = DataCollector(
            model_reporters={
                "Step": lambda m: m.steps,
                "Top 10": self.top_10_skill,
                "Bottom 10": self.bottom_10_skill,
            }
        )

    def step(self):
        self.steps += 1

        for agent in list(self.agents):
            agent.step()

        self.datacollector.collect(self)

    def top_10_skill(self):
        agents = sorted(self.agents, key=lambda a: a.wealth)
        k = max(1, int(0.1 * len(agents)))
        top = agents[-k:]
        return sum(a.skill for a in top) / k

    def bottom_10_skill(self):
        agents = sorted(self.agents, key=lambda a: a.wealth)
        k = max(1, int(0.1 * len(agents)))
        bottom = agents[:k]
        return sum(a.skill for a in bottom) / k
