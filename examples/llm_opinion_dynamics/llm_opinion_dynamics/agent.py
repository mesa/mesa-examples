from mesa_llm.llm_agent import LLMAgent
from mesa_llm.reasoning.reasoning import Reasoning


class OpinionAgent(LLMAgent):
    """
    An LLM-powered agent that holds an opinion on a topic and can be
    persuaded by neighboring agents through natural language debate.

    Attributes:
        opinion (float): Current opinion score between 0.0 and 10.0.
        topic (str): The topic being debated.
    """

    def __init__(self, model, reasoning: type[Reasoning], opinion: float, topic: str):
        system_prompt = f"""You are an agent in a social simulation debating the topic: '{topic}'.
Your current opinion score is {opinion:.1f} out of 10 (0=strongly against, 10=strongly for).
When you interact with neighbors:
1. Read their opinion and argument carefully.
2. If their argument is convincing, update your internal_state 'opinion' score closer to theirs.
3. If unconvincing, keep your score or move slightly away.
4. Always respond with your updated opinion score as a number between 0 and 10.
Be concise. Your reasoning should reflect genuine persuasion dynamics."""

        super().__init__(
            model=model,
            reasoning=reasoning,
            system_prompt=system_prompt,
            vision=1,
            internal_state=["opinion"],
        )
        self.opinion = opinion
        self.topic = topic

    def step(self):
        """Each step, observe neighbors and potentially update opinion."""
        obs = self.generate_obs()

        # Only debate if there are neighbors
        if not obs.local_state:
            return

        # Build a prompt summarizing neighbor opinions
        neighbor_summary = "\n".join(
            f"- Agent {uid}: opinion={info['internal_state']}"
            for uid, info in obs.local_state.items()
        )

        step_prompt = f"""Your current opinion on '{self.topic}' is {self.opinion:.1f}/10.

Your neighbors' opinions:
{neighbor_summary}

Based on these interactions, decide whether to update your opinion score.
Respond with ONLY a single number between 0.0 and 10.0 representing your new opinion."""

        plan = self.reasoning.plan(obs, step_prompt=step_prompt)

        # Parse the LLM response to extract updated opinion
        try:
            response_text = ""
            if hasattr(plan, "llm_plan") and plan.llm_plan:
                for block in plan.llm_plan:
                    if hasattr(block, "text"):
                        response_text += block.text
            # Extract first float found in response
            import re
            numbers = re.findall(r"\b\d+\.?\d*\b", response_text)
            if numbers:
                new_opinion = float(numbers[0])
                new_opinion = max(0.0, min(10.0, new_opinion))
                self.opinion = new_opinion
                self.internal_state = [f"opinion:{self.opinion:.1f}"]
        except (ValueError, IndexError):
            pass  # Keep current opinion if parsing fails
