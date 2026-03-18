from concurrent.futures import ThreadPoolExecutor

from mesa import Model
from mesa.datacollection import DataCollector
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
        self.cooperation_rate = 0.0
        self.total_cooperations = 0
        self.total_defections = 0

        # Create agents
        for _ in range(num_agents):
            agent = PrisonerAgent(model=self, llm_model=llm_model)
            agent.memory = ShortTermMemory(agent=agent, n=5, display=False)
            agent._update_internal_state()

        # Data collection
        self.datacollector = DataCollector(
            model_reporters={
                "cooperation_rate": "cooperation_rate",
                "total_cooperations": "total_cooperations",
                "total_defections": "total_defections",
            },
            agent_reporters={
                "score": "score",
                "last_action": "last_action",
            },
        )
        self.datacollector.collect(self)

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

    def _get_agent_action(self, agent) -> tuple:
        """Fetch a single agent's LLM decision. Designed for concurrent execution."""
        agent._update_internal_state()
        plan = agent.reasoning_instance.plan(obs=agent.generate_obs())
        content = str(plan.llm_plan.content) if hasattr(plan.llm_plan, "content") else str(plan.llm_plan)
        return agent, agent._parse_action(content)

    def step(self) -> None:
        """
        Advance the model by one round.

        All agents reason concurrently (ThreadPoolExecutor) so LLM calls
        are parallelised and no agent observes another's mid-step state
        changes before decisions are locked in. Outcomes are applied only
        after every agent has committed to an action.
        """
        super().step()
        pairs = self._pair_agents()
        paired_agents = [a for pair in pairs for a in pair]

        # Phase 1 — all agents think in parallel (no dirty reads, no UI freeze)
        with ThreadPoolExecutor(max_workers=len(paired_agents)) as executor:
            agent_actions = dict(executor.map(self._get_agent_action, paired_agents))

        # Phase 2 — apply outcomes simultaneously after all decisions are locked
        round_cooperations = 0
        round_defections = 0

        for agent1, agent2 in pairs:
            action1 = agent_actions[agent1]
            action2 = agent_actions[agent2]

            agent1.apply_decision(action1, action2)
            agent2.apply_decision(action2, action1)

            round_cooperations += (action1 == "cooperate") + (action2 == "cooperate")
            round_defections += (action1 == "defect") + (action2 == "defect")

        self._update_stats(round_cooperations, round_defections)
        self.datacollector.collect(self)
