from mesa_llm.llm_agent import LLMAgent
from mesa_llm.reasoning.cot import CoTReasoning

SYSTEM_PROMPT = """You are a person living in a community during an epidemic outbreak.
You must decide how to behave based on your current health status and what you observe
around you. Your decisions directly affect your own health and the health of others.

You can take the following actions:
- isolate: Stay home, avoid all contact. Reduces infection risk but limits social life.
- move_freely: Go about normal activities. Higher infection risk if near infected people.
- seek_treatment: If infected, seek medical help to recover faster.

Make decisions that balance your personal wellbeing with community responsibility."""


class EpidemicAgent(LLMAgent):
    """
    An agent in an epidemic simulation that uses LLM Chain-of-Thought reasoning
    to decide whether to isolate, move freely, or seek treatment.

    Health states:
        - susceptible: Healthy but can be infected
        - infected: Currently sick and contagious
        - recovered: Recovered and immune

    Attributes:
        health_state (str): Current health state of the agent.
        days_infected (int): Number of steps the agent has been infected.
        isolation_days (int): Number of steps the agent has been isolating.
        is_isolating (bool): Whether the agent is currently isolating.
    """

    def __init__(self, model, health_state: str = "susceptible"):
        super().__init__(
            model=model,
            reasoning=CoTReasoning,
            system_prompt=SYSTEM_PROMPT,
            vision=2,
            internal_state=[f"health_state:{health_state}"],
            step_prompt=(
                "Based on your current health state and what you observe around you, "
                "decide your next action. Should you isolate, move freely, or seek treatment? "
                "Think carefully about the risks to yourself and others."
            ),
        )
        self.health_state: str = health_state
        self.days_infected: int = 0
        self.isolation_days: int = 0
        self.is_isolating: bool = False

    def _update_internal_state(self) -> None:
        """Sync internal_state list with current health attributes for LLM observation."""
        self.internal_state = [
            f"health_state:{self.health_state}",
            f"days_infected:{self.days_infected}",
            f"is_isolating:{self.is_isolating}",
        ]

    def _parse_action(self, tool_responses: list) -> str:
        """
        Extract the chosen action from LLM tool responses.

        Falls back to 'move_freely' if no recognized action is found.
        """
        for response in tool_responses:
            content = str(response).lower()
            if "isolate" in content:
                return "isolate"
            if "seek_treatment" in content or "treatment" in content:
                return "seek_treatment"
            if "move_freely" in content or "move freely" in content:
                return "move_freely"
        return "move_freely"

    def _apply_action(self, action: str) -> None:
        """Apply the chosen action to update agent state."""
        if action == "isolate":
            self.is_isolating = True
            self.isolation_days += 1
        elif action == "seek_treatment":
            self.is_isolating = True
            if self.health_state == "infected":
                # Treatment accelerates recovery
                self.days_infected += 2
        else:
            self.is_isolating = False

    def _update_health(self) -> None:
        """Update health state based on current condition and interactions."""
        if self.health_state == "infected":
            self.days_infected += 1
            # Recover after 7-10 days
            recovery_threshold = 7 if self.is_isolating else 10
            if self.days_infected >= recovery_threshold:
                self.health_state = "recovered"
                self.days_infected = 0
                self.is_isolating = False

        elif self.health_state == "susceptible" and not self.is_isolating:
            # Check for infected agents in spatial neighborhood (Moore radius=1).
            # vision=2 lets the LLM observe a wider area; infection requires
            # direct contact with an immediate neighbor.
            infected_neighbors = []
            if hasattr(self, "cell") and self.cell is not None:
                for neighbor_cell in self.cell.connections.values():
                    for agent in neighbor_cell.agents:
                        if (
                            hasattr(agent, "health_state")
                            and agent.health_state == "infected"
                            and not agent.is_isolating
                        ):
                            infected_neighbors.append(agent)
            infection_probability = min(0.3 * len(infected_neighbors), 0.9)
            if self.model.random.random() < infection_probability:
                self.health_state = "infected"
                self.internal_state = [f"health_state:{self.health_state}"]
