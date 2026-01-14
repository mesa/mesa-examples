from mesa import Agent


class OpinionAgent(Agent):
    """An agent with a continuous opinion value.

    Each agent holds a continuous opinion value in the range (-1, 1).
    When interacting with another agent, the agent updates its opinion
    by moving it toward the other agent's opinion.

    Attributes:
        opinion (float): The agent's current opinion value in the range (-1, 1)
    """

    opinion: float

    def __init__(self, model, opinion):
        """Create a new opinion agent.

        Args:
            model (Model): The Mesa model instance.
            opinion (float): Initial opinion value for the agent.
        """
        super().__init__(model)
        self.opinion = opinion

    def update_opinion(self, other_opinion, mu):
        """Update the agent's opinion toward another opinion.

        Args:
            other_opinion (float): Opinion value of the interacting agent.
            mu (float): Convergence rate controlling the strength of adjustment.
        """
        self.opinion += mu * (other_opinion - self.opinion)
