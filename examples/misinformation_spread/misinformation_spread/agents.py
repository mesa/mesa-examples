import mesa
from mesa.discrete_space.cell_agent import BasicMovement, HasCell
from mesa_llm.llm_agent import LLMAgent
from mesa_llm.reasoning.react import ReActReasoning

from misinformation_spread.tools import (  # noqa: F401 — import so @tool registers them
    challenge_rumor,
    check_neighbors,
    spread_rumor,
    update_belief,
)


class CitizenAgent(LLMAgent, HasCell, BasicMovement):
    def __init__(self, model, name, persona, initial_stance, initial_belief):
        super().__init__(
            model=model,
            reasoning=ReActReasoning,
            llm_model=model.llm_model,
            system_prompt=(
                f"You are {name}, a citizen in a small community. {persona}"
            ),
        )
        # Remove built-in movement tools that confuse the small LLM
        # We only want our custom tools (check_neighbors, spread_rumor,
        # challenge_rumor, update_belief) for communication
        for tool_name in ["move_one_step", "teleport_to_location", "speak_to"]:
            self.tool_manager.tools.pop(tool_name, None)

        self.name = name
        self.stance = initial_stance
        self.belief_score = initial_belief

    def step(self):
        prompt = (
            f"You are currently a {self.stance} with belief score {self.belief_score:.2f}.\n"
            f'The rumor is: "{self.model.rumor}"\n\n'
            f"You MUST follow these steps in order:\n"
            f"Step 1: Call check_neighbors to see who is nearby. Look at the agent IDs in the result.\n"
            f"Step 2: Pick ONE agent ID from the check_neighbors result. "
            f"If your belief score is above 0.5, call spread_rumor with that agent's ID. "
            f"If your belief score is 0.5 or below, call challenge_rumor with that agent's ID. "
            f"IMPORTANT: Only use agent IDs that appeared in the check_neighbors result.\n"
            f"Step 3: Call update_belief with a new score. "
            f"If you spread the rumor, increase your score slightly (add 0.05). "
            f"If you challenged it, decrease your score slightly (subtract 0.05).\n"
        )
        plan = self.reasoning.plan(prompt=prompt)
        self.apply_plan(plan)

        # Workaround: small LLMs (e.g. Gemma 3 1B) struggle with multi-step
        # ReAct tool calling — they often skip update_belief or hallucinate
        # agent IDs. We apply belief updates programmatically based on which
        # communication tool the LLM actually invoked.
        # The plan object stores tool calls at plan.llm_plan.tool_calls,
        # where each entry is a ChatCompletionMessageToolCall with
        # .function.name for the tool name.
        tool_calls = getattr(getattr(plan, "llm_plan", None), "tool_calls", None)
        if tool_calls:
            called_tools = {tc.function.name for tc in tool_calls}
            if "spread_rumor" in called_tools:
                self.belief_score = min(1.0, self.belief_score + 0.05)
            elif "challenge_rumor" in called_tools:
                self.belief_score = max(0.0, self.belief_score - 0.05)

            # Update stance based on new score
            if self.belief_score > 0.7:
                self.stance = "believer"
            elif self.belief_score < 0.3:
                self.stance = "skeptic"
            else:
                self.stance = "neutral"


class RuleBasedAgent(mesa.Agent, HasCell, BasicMovement):
    def __init__(self, model, name, persona, initial_stance, initial_belief):
        super().__init__(model=model)
        self.name = name
        self.stance = initial_stance
        self.belief_score = initial_belief

    def step(self):
        neighbors = [agent for cell in self.cell.neighborhood for agent in cell.agents]

        for neighbor in neighbors:
            if neighbor.stance == "believer":
                self.belief_score += 0.1 * (1 - self.belief_score)
            elif neighbor.stance == "skeptic":
                self.belief_score -= 0.1 * self.belief_score
            else:
                self.belief_score += self.random.uniform(-0.02, 0.02)

        self.belief_score = max(0.0, min(1.0, self.belief_score))

        if self.belief_score > 0.7:
            self.stance = "believer"
        elif self.belief_score < 0.3:
            self.stance = "skeptic"
        else:
            self.stance = "neutral"
