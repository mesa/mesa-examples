import re

from mesa_llm.llm_agent import LLMAgent
from mesa_llm.reasoning.cot import CoTReasoning

SYSTEM_PROMPT = """You are a player in an iterated Prisoner's Dilemma game.

Each round you interact with a partner. You must choose one of two actions:
- cooperate: Work together for mutual benefit. If both cooperate, both gain moderately.
- defect: Betray your partner for personal gain. If you defect and they cooperate,
  you gain a lot and they gain nothing. If both defect, both gain very little.

Payoff matrix (your score, partner score):
- Both cooperate:       (3, 3) — mutual benefit
- You defect, they cooperate: (5, 0) — you exploit them
- You cooperate, they defect: (0, 5) — they exploit you
- Both defect:          (1, 1) — mutual punishment

Your goal is to maximize your total score over multiple rounds.
Consider your partner's history when making decisions.
Think carefully about trust, reputation, and long-term strategy.

IMPORTANT: You MUST end your response with exactly one of these two lines:
<ACTION>: COOPERATE
<ACTION>: DEFECT"""


class PrisonerAgent(LLMAgent):
    """
    An agent in an iterated Prisoner's Dilemma simulation that uses
    LLM Chain-of-Thought reasoning to decide whether to cooperate or defect.

    Unlike fixed-strategy agents (always defect, tit-for-tat, etc.),
    this agent reasons about its partner's history, trust, and long-term
    payoff to make nuanced decisions.

    Attributes:
        score (int): Cumulative score across all rounds.
        last_action (str): Action taken in the most recent round.
        cooperation_count (int): Total number of times agent cooperated.
        defection_count (int): Total number of times agent defected.
        round_history (list): List of (action, partner_action, payoff) tuples.
    """

    # Payoff matrix
    PAYOFFS = {
        ("cooperate", "cooperate"): (3, 3),
        ("cooperate", "defect"): (0, 5),
        ("defect", "cooperate"): (5, 0),
        ("defect", "defect"): (1, 1),
    }

    def __init__(self, model, llm_model: str = "gemini/gemini-2.0-flash") -> None:
        super().__init__(
            model=model,
            reasoning=CoTReasoning,
            llm_model=llm_model,
            system_prompt=SYSTEM_PROMPT,
            vision=0,
            internal_state=["score:0", "last_action:none", "rounds_played:0"],
            step_prompt=(
                "You are about to play a round of Prisoner's Dilemma. "
                "Review your history and your partner's behavior. "
                "Should you cooperate or defect this round? "
                "Think carefully about trust, reputation, and long-term strategy."
            ),
        )
        self.score: int = 0
        self.last_action: str = "none"
        self.cooperation_count: int = 0
        self.defection_count: int = 0
        self.round_history: list = []

    def _update_internal_state(self) -> None:
        """Sync internal state for LLM observation."""
        total_rounds = self.cooperation_count + self.defection_count
        coop_rate = (
            round(self.cooperation_count / total_rounds, 2) if total_rounds > 0 else 0
        )
        self.internal_state = [
            f"score:{self.score}",
            f"last_action:{self.last_action}",
            f"cooperation_rate:{coop_rate}",
            f"rounds_played:{total_rounds}",
        ]

    def _parse_action(self, plan_content: str) -> str:
        """
        Extract cooperate/defect decision from LLM response.

        Looks for the mandatory <ACTION>: COOPERATE or <ACTION>: DEFECT tag
        that the system prompt requires at the end of every response.
        Falls back to cooperate if the tag is missing or malformed.

        Args:
            plan_content: Raw LLM response text.

        Returns:
            Either 'cooperate' or 'defect'.
        """
        match = re.search(r"<ACTION>\s*:\s*(COOPERATE|DEFECT)", plan_content, re.IGNORECASE)
        if match:
            return match.group(1).lower()
        return "cooperate"

    def apply_decision(self, action: str, partner_action: str) -> None:
        """
        Apply the outcome of a round given both agents' actions.

        Args:
            action: This agent's action ('cooperate' or 'defect').
            partner_action: Partner's action ('cooperate' or 'defect').
        """
        my_payoff, _ = self.PAYOFFS.get((action, partner_action), (0, 0))
        self.score += my_payoff
        self.last_action = action

        if action == "cooperate":
            self.cooperation_count += 1
        else:
            self.defection_count += 1

        self.round_history.append((action, partner_action, my_payoff))
        self._update_internal_state()
