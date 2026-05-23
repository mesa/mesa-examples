from mesa_llm.llm_agent import LLMAgent
from mesa_llm.tools.tool_manager import ToolManager

# One shared ToolManager for all CountryAgents.
# Custom negotiation tools (make_proposal, etc.) are registered into this
# manager by tools.py at import time via @tool(tool_manager=country_tool_manager).
# The global inbuilt tools (speak_to, move_one_step, …) are automatically
# copied into every ToolManager at construction time.
country_tool_manager = ToolManager()


def get_negotiation_history(agent, max_messages: int = 6) -> str:
    """Extract the most recent negotiation messages from an agent's short-term memory.

    Args:
        agent: The CountryAgent whose memory to read.
        max_messages: Maximum number of messages to return.

    Returns:
        A formatted string of recent messages, oldest first.
    """
    messages = []

    memory_source = None
    if hasattr(agent.memory, "short_term_memory"):
        memory_source = agent.memory.short_term_memory
    elif hasattr(agent.memory, "memory_entries"):
        memory_source = agent.memory.memory_entries

    if memory_source:
        entries_to_check = min(len(memory_source), max_messages * 2)
        for entry in reversed(list(memory_source)[-entries_to_check:]):
            if len(messages) >= max_messages:
                break
            if isinstance(entry.content, dict) and "message" in entry.content:
                sender_id = entry.content.get("sender", "Unknown")
                msg = entry.content.get("message", "")
                try:
                    sender_agent = next(
                        a for a in agent.model.agents if a.unique_id == sender_id
                    )
                    sender_name = getattr(
                        sender_agent, "country_name", f"Agent {sender_id}"
                    )
                except StopIteration:
                    sender_name = f"Agent {sender_id}"
                messages.append(f"  {sender_name}: {msg}")

    messages.reverse()
    return "\n".join(messages) if messages else "  No messages yet."


class CountryAgent(LLMAgent):
    """An LLM-powered country agent in a climate negotiation simulation.

    Each agent represents a country with unique economic and environmental
    characteristics.  Agents communicate via speak_to and four custom
    negotiation tools (make_proposal, accept_proposal, form_coalition,
    reject_and_counter).  vision=-1 means every agent observes all other
    agents — modelling a plenary negotiating room.

    Attributes:
        country_name: Human-readable country label (e.g. "EU").
        emissions_per_capita: Annual CO₂ emissions per person in tonnes.
        gdp_per_capita: GDP per person in USD.
        development_status: "developed" or "developing".
        current_pledge: Percentage emissions reduction the agent has pledged.
        coalition_members: unique_ids of countries in the same coalition.
        accepted_treaty: True when the agent has formally accepted a treaty.
        proposals_made: Total proposals and counter-proposals made.
        proposals_accepted: Total proposals formally accepted.
    """

    def __init__(
        self,
        model,
        reasoning,
        llm_model: str,
        country_name: str,
        system_prompt: str,
        emissions_per_capita: float,
        gdp_per_capita: float,
        development_status: str,
    ):
        super().__init__(
            model=model,
            reasoning=reasoning,
            llm_model=llm_model,
            system_prompt=system_prompt,
            vision=-1,
            internal_state=[
                f"country:{country_name}",
                f"emissions_per_capita_tCO2:{emissions_per_capita}",
                f"gdp_per_capita_usd:{gdp_per_capita}",
                f"development_status:{development_status}",
            ],
        )
        self.tool_manager = country_tool_manager

        self.country_name = country_name
        self.emissions_per_capita = emissions_per_capita
        self.gdp_per_capita = gdp_per_capita
        self.development_status = development_status

        self.current_pledge: float = 0.0
        self.coalition_members: list[int] = []
        self.accepted_treaty: bool = False
        self.proposals_made: int = 0
        self.proposals_accepted: int = 0

    def step(self):
        observation = self.generate_obs()
        negotiation_history = get_negotiation_history(self)

        id_to_name = {
            a.unique_id: getattr(a, "country_name", f"Agent {a.unique_id}")
            for a in self.model.agents
        }
        other_status_lines = []
        for a in self.model.agents:
            if a is not self and isinstance(a, CountryAgent):
                coalition_names = [
                    id_to_name.get(i, str(i)) for i in a.coalition_members
                ]
                other_status_lines.append(
                    f"  {a.country_name} (ID {a.unique_id}): "
                    f"pledge={float(a.current_pledge):.1f}%, "
                    f"coalition={coalition_names or 'none'}, "
                    f"accepted={a.accepted_treaty}"
                )
        other_status = "\n".join(other_status_lines) or "  No data yet."

        # Build a concise ID→name reference to help smaller LLMs avoid hallucinating IDs.
        id_reference = ", ".join(
            f"{a.unique_id}={getattr(a, 'country_name', str(a.unique_id))}"
            for a in self.model.agents
        )

        prompt = (
            f"NEGOTIATION ROUND {self.model.steps}\n\n"
            f"VALID COUNTRY IDs — use ONLY these integers for partner_ids and proposer_id:\n"
            f"  {id_reference}\n\n"
            f"YOUR STATUS:\n"
            f"  Country: {self.country_name} (your ID: {self.unique_id})\n"
            f"  Emissions per capita: {self.emissions_per_capita} tCO2/year\n"
            f"  GDP per capita: ${self.gdp_per_capita:,.0f}\n"
            f"  Development status: {self.development_status}\n"
            f"  Current pledge: {self.current_pledge:.1f}% reduction by 2035\n"
            f"  Your coalition members (their IDs): {self.coalition_members or 'none'}\n"
            f"  Treaty accepted: {self.accepted_treaty}\n\n"
            f"OTHER COUNTRIES AT THE TABLE:\n{other_status}\n\n"
            f"RECENT NEGOTIATIONS:\n{negotiation_history}\n\n"
            f"INSTRUCTIONS:\n"
            f"You are {self.country_name}'s chief climate negotiator at the Global "
            f"Climate Summit. Choose ONE action this round:\n"
            f"  speak_to send a targeted diplomatic message to one or more "
            f"countries (use their integer IDs from the VALID COUNTRY IDs list above)\n"
            f"  make_proposal formally propose a reduction target to all parties\n"
            f"  accept_proposal accept another country's proposal if it is acceptable\n"
            f"  form_coalition build an alliance with countries that share your stance\n"
            f"  reject_and_counter reject an unreasonable proposal with a counter-offer\n\n"
            f"A treaty is reached when at least 2/3 of countries have accepted a common "
            f"proposal.  Balance your national economic interests with global climate "
            f"responsibility.  Be strategic: build alliances before making proposals."
        )

        plan = self.reasoning.plan(
            prompt=prompt,
            obs=observation,
            selected_tools=[
                "speak_to",
                "make_proposal",
                "accept_proposal",
                "form_coalition",
                "reject_and_counter",
            ],
        )
        self.apply_plan(plan)
