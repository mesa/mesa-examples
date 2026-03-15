from mesa import Model
from mesa_llm.memory.st_memory import ShortTermMemory

from .agent import PrisonerAgent


class PrisonersDilemmaModel(Model):
    """
    An iterated Prisoner's Dilemma simulation where agents use LLM
    Chain-of-Thought reasoning to decide whether to cooperate or defect.

    Unlike classical fixed-strategy models (always defect, tit-for-tat,
    random), agents here reason about their partner's history, trust signals,
    and long-term payoff strategy — producing emergent negotiation behavior
    that fixed rules cannot capture.

    Each step, agents are paired randomly. Both decide simultaneously
    whether to cooperate or defect. Payoffs are applied and scores updated.
    Over many rounds, patterns of trust, exploitation, and reputation emerge.

    Attributes:
        num_agents (int): Number of agents in the simulation.
        round_number (int): Current round number.
        cooperation_rate (float): Fraction of cooperative actions this round.
        total_cooperations (int): Cumulative cooperation count.
        total_defections (int): Cumulative defection count.

    Reference:
        Axelrod, R. (1984). The Evolution of Cooperation. Basic Books.
    """

    def __init__(
        self,
        num_agents: int = 6,
        llm_model: str = "gemini/gemini-2.0-flash",
    ) -> None:
        super().__init__()

        self.num_agents = num_agents
        self.round_number = 0
        self.cooperation_rate = 0.0
        self.total_cooperations = 0
        self.total_defections = 0

        # Create agents
        for _ in range(num_agents):
            agent = PrisonerAgent(model=self, llm_model=llm_model)
            agent.memory = ShortTermMemory(agent=agent, n=5, display=False)
            agent._update_internal_state()

    def _pair_agents(self) -> list[tuple]:
        """
        Randomly pair agents for this round.

        Returns:
            List of (agent1, agent2) tuples.
        """
        agents = list(self.agents)
        self.random.shuffle(agents)
        pairs = []
        for i in range(0, len(agents) - 1, 2):
            pairs.append((agents[i], agents[i + 1]))
        return pairs

    def _update_stats(self, round_cooperations: int, round_defections: int) -> None:
        """Update model-level statistics after each round."""
        self.total_cooperations += round_cooperations
        self.total_defections += round_defections
        total = round_cooperations + round_defections
        self.cooperation_rate = round_cooperations / total if total > 0 else 0.0

    def step(self) -> None:
        """
        Advance the model by one round.

        Each agent reasons about their decision, then pairs are revealed
        and payoffs applied simultaneously.
        """
        self.round_number += 1
        pairs = self._pair_agents()

        round_cooperations = 0
        round_defections = 0

        for agent1, agent2 in pairs:
            # Both agents update their state before deciding
            agent1._update_internal_state()
            agent2._update_internal_state()

            # Both agents reason independently using LLM
            plan1 = agent1.reasoning.plan(obs=agent1.generate_obs())
            plan2 = agent2.reasoning.plan(obs=agent2.generate_obs())

            # Extract decisions from LLM plans
            plan1_content = str(plan1.llm_plan.content) if hasattr(plan1.llm_plan, "content") else str(plan1.llm_plan)
            plan2_content = str(plan2.llm_plan.content) if hasattr(plan2.llm_plan, "content") else str(plan2.llm_plan)

            action1 = agent1._parse_action(plan1_content)
            action2 = agent2._parse_action(plan2_content)

            # Apply outcomes
            agent1.apply_decision(action1, action2)
            agent2.apply_decision(action2, action1)

            if action1 == "cooperate":
                round_cooperations += 1
            else:
                round_defections += 1

            if action2 == "cooperate":
                round_cooperations += 1
            else:
                round_defections += 1

        self._update_stats(round_cooperations, round_defections)
