import statistics

from mesa import Model
from mesa.datacollection import DataCollector

from .agents import InvestorAgent


class TradingDWModel(Model):
    def __init__(self, n=100, epsilon=0.2, mu=0.5, transaction_cost=2.0, rng=None):
        super().__init__(rng=rng)
        self.n = n
        self.epsilon = epsilon
        self.mu = mu
        self.transaction_cost = transaction_cost
        self.attempted_interactions = 0
        self.accepted_interactions = 0

        self.datacollector = DataCollector(
            model_reporters={
                "Variance": self.compute_variance,
                "Avg Gross Wealth": lambda m: statistics.mean(
                    [a.gross_wealth for a in m.agents]
                )
                if m.agents
                else 0,
                "Avg Net Wealth": lambda m: statistics.mean(
                    [a.net_wealth for a in m.agents]
                )
                if m.agents
                else 0,
            },
            agent_reporters={
                "opinion": "opinion",
                "net_wealth": "net_wealth",
                "confidence": "confidence",
                "trades": "trades",
            },
        )

        for _ in range(self.n):
            op = self.random.uniform(-1, 1)
            conf = self.random.uniform(1.0, 5.0)
            agent = InvestorAgent(self, op, conf)
            self.agents.add(agent)

        self.datacollector.collect(self)

    def step(self):
        agent_list = list(self.agents)

        # Simulating Natural Market Volatility Returns (Random Walk with Positive Drift
        market_return = self.random.normalvariate(0.001, 0.01)
        for agent in agent_list:
            agent.gross_wealth *= 1 + market_return
            agent.net_wealth *= 1 + market_return

        for _ in range(self.n):
            agent_a, agent_b = self.random.sample(agent_list, 2)
            self.attempted_interactions += 1

            # Banerjee: Communication within cognitive thresholds leads to opinion convergence (herd formation).
            if abs(agent_a.opinion - agent_b.opinion) < self.epsilon:
                old_op_a = agent_a.opinion
                agent_a.update_opinion(agent_b.opinion, self.mu)
                agent_b.update_opinion(old_op_a, self.mu)

                agent_a.execute_trade()
                agent_b.execute_trade()
                self.accepted_interactions += 1

        self.datacollector.collect(self)

    def compute_variance(self):
        opinions = [a.opinion for a in self.agents]
        return statistics.variance(opinions) if len(opinions) > 1 else 0
