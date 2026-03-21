import logging

from mesa_llm.llm_agent import LLMAgent
from mesa_llm.reasoning.reasoning import Reasoning

logger = logging.getLogger(__name__)


class SchellingAgent(LLMAgent):
    """
    An LLM-powered agent in the Schelling Segregation model.

    Unlike the classical Schelling model where agents move if fewer than
    a fixed fraction of neighbors share their group, this agent reasons
    about its neighborhood using an LLM and decides whether it feels
    comfortable staying or wants to move.

    Attributes:
        group (int): The agent's group identity (0 or 1).
        is_happy (bool): Whether the agent is satisfied with its location.
    """

    def __init__(self, model, reasoning: type[Reasoning], group: int):
        group_label = "Group A" if group == 0 else "Group B"
        other_label = "Group B" if group == 0 else "Group A"

        system_prompt = f"""You are an agent in a social simulation. You belong to {group_label}.
You are deciding whether you feel comfortable in your current neighborhood.
Look at your neighbors: if too many belong to {other_label} and too few to {group_label},
you may feel uncomfortable and want to move.
Respond with ONLY one word: 'happy' if you want to stay, or 'unhappy' if you want to move."""

        super().__init__(
            model=model,
            reasoning=reasoning,
            system_prompt=system_prompt,
            vision=1,
            internal_state=["group", "is_happy"],
        )
        self.group = group
        self.is_happy = True

    def step(self):
        """Decide whether to move based on LLM reasoning about neighborhood."""
        obs = self.generate_obs()

        # Count neighbors by group
        neighbors = list(self.cell.neighborhood.agents) if self.cell else []
        same = sum(
            1 for n in neighbors if hasattr(n, "group") and n.group == self.group
        )
        total = len(neighbors)
        different = total - same

        if total == 0:
            self.is_happy = True
            self.internal_state = [f"group:{self.group}", "is_happy:True"]
            return

        group_label = "Group A" if self.group == 0 else "Group B"
        other_label = "Group B" if self.group == 0 else "Group A"

        step_prompt = f"""You belong to {group_label}.
Your current neighborhood has:
- {same} neighbors from {group_label} (your group)
- {different} neighbors from {other_label} (the other group)
- {total} neighbors total

Do you feel comfortable here, or do you want to move to a different location?
Respond with ONLY one word: 'happy' or 'unhappy'."""

        plan = self.reasoning.plan(obs, step_prompt=step_prompt)

        # Parse LLM response
        response_text = ""
        try:
            if hasattr(plan, "llm_plan") and plan.llm_plan:
                for block in plan.llm_plan:
                    if hasattr(block, "text"):
                        response_text += block.text.lower()
        except Exception as e:
            logger.warning("Failed to parse LLM response: %s", e)

        self.is_happy = "unhappy" not in response_text
        self.internal_state = [
            f"group:{self.group}",
            f"is_happy:{self.is_happy}",
        ]

        # If unhappy, move to a random empty cell
        if not self.is_happy:
            empty_cells = [
                cell
                for cell in self.model.grid.all_cells
                if len(list(cell.agents)) == 0
            ]
            if empty_cells:
                new_cell = self.model.random.choice(empty_cells)
                self.cell = new_cell
                self.pos = new_cell.coordinate
