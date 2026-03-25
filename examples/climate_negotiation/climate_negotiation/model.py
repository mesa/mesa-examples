from mesa.datacollection import DataCollector
from mesa.model import Model
from rich import print as rprint

from .agents import CountryAgent
from mesa_llm.reasoning.reasoning import Reasoning

COUNTRIES: list[dict] = [
    {
        "country_name": "USA",
        "emissions_per_capita": 14.5,
        "gdp_per_capita": 65_000,
        "development_status": "developed",
        "system_prompt": (
            "You are the USA's chief climate negotiator. "
            "The USA is the largest historical emitter with a $65k GDP per capita. "
            "You support climate action but insist all major economies — especially "
            "China and India — commit to comparable reductions. You prefer "
            "market-based mechanisms and oppose unilateral economic disadvantages."
        ),
    },
    {
        "country_name": "EU",
        "emissions_per_capita": 6.4,
        "gdp_per_capita": 35_000,
        "development_status": "developed",
        "system_prompt": (
            "You are the EU's chief climate negotiator. "
            "The EU targets a 55% reduction by 2030 and leads global climate ambition. "
            "You push for legally binding targets for all developed nations and "
            "substantial financial support for developing nations. "
            "Actively build coalitions with high-ambition partners."
        ),
    },
    {
        "country_name": "China",
        "emissions_per_capita": 7.1,
        "gdp_per_capita": 12_000,
        "development_status": "developing",
        "system_prompt": (
            "You are China's chief climate negotiator. "
            "China is the world's largest current emitter but still a developing "
            "economy at $12k GDP per capita. You argue that developed nations caused "
            "most historical emissions and must bear greater financial burdens. "
            "You support long-term goals but resist targets that constrain development "
            "without adequate technology transfer and green finance from rich countries."
        ),
    },
    {
        "country_name": "India",
        "emissions_per_capita": 1.9,
        "gdp_per_capita": 2_200,
        "development_status": "developing",
        "system_prompt": (
            "You are India's chief climate negotiator. "
            "India has very low per-capita emissions (1.9 tCO2) and a $2.2k GDP. "
            "You firmly defend common but differentiated responsibilities. "
            "India needs fossil fuel access to develop. You support renewables "
            "but reject targets that deny energy access to 1.4 billion people. "
            "Form strong coalitions with other developing nations."
        ),
    },
    {
        "country_name": "Brazil",
        "emissions_per_capita": 2.2,
        "gdp_per_capita": 8_600,
        "development_status": "developing",
        "system_prompt": (
            "You are Brazil's chief climate negotiator. "
            "Brazil's emissions are driven by deforestation, not fossil fuels. "
            "You argue that forest conservation and biodiversity protection must "
            "count formally as climate action. You seek payment for ecosystem "
            "services and will only accept ambitious targets if forest credits "
            "are explicitly recognised in the treaty text."
        ),
    },
    {
        "country_name": "Russia",
        "emissions_per_capita": 11.4,
        "gdp_per_capita": 12_000,
        "development_status": "developed",
        "system_prompt": (
            "You are Russia's chief climate negotiator. "
            "Russia is a major fossil fuel exporter with 11.4 tCO2 per capita. "
            "You accept climate science but argue for gradual, technology-led "
            "transitions. You resist aggressive near-term targets that threaten "
            "your fossil fuel revenues. You may agree to modest pledges if given "
            "long timelines and substantial technology support."
        ),
    },
]


class ClimateNegotiationModel(Model):
    """Multi-agent LLM climate treaty negotiation model.

    Six country agents negotiate a shared emissions-reduction target over
    multiple rounds.  The model tracks proposal counts, acceptance rates,
    coalition formation, and whether a treaty consensus has emerged.

    Mesa-LLM features demonstrated
    - STLTMemory   : short-term stores recent proposals; long-term consolidates
                     committed positions across rounds.
    - ReActReasoning: agents reason then act within each simulation step.
    - speak_to     : inbuilt diplomatic messaging tool between agents.
    - Custom tools  : make_proposal, accept_proposal, form_coalition,
                      reject_and_counter.
    - vision=-1    : agents observe all other parties (full-room awareness,
                     no spatial grid needed).

    Args:
        reasoning: Reasoning strategy class (e.g. ReActReasoning, CoTReasoning).
        llm_model: LiteLLM model string, e.g. ``"gemini/gemini-2.0-flash"``
                   or ``"openai/gpt-4o-mini"``.
        rng: Random seed for reproducibility.
    """

    def __init__(
        self,
        reasoning: type[Reasoning],
        llm_model: str = "gemini/gemini-2.0-flash",
        rng: int = 42,
    ):
        super().__init__(rng=rng)

        # Global negotiation counters - updated by the tool functions
        self.total_proposals: int = 0
        self.total_acceptances: int = 0

        # Create one CountryAgent per country profile
        for config in COUNTRIES:
            CountryAgent(
                model=self,
                reasoning=reasoning,
                llm_model=llm_model,
                **config,
            )

        self.datacollector = DataCollector(
            model_reporters={
                "TotalProposals": lambda m: m.total_proposals,
                "TotalAcceptances": lambda m: m.total_acceptances,
                "TreatyReached": lambda m: int(m._treaty_reached()),
                "AveragePledge": lambda m: m._average_pledge(),
                "LargestCoalitionSize": lambda m: m._largest_coalition(),
            },
            agent_reporters={
                "CurrentPledge": "current_pledge",
                "AcceptedTreaty": lambda a: int(a.accepted_treaty),
                "CoalitionSize": lambda a: len(a.coalition_members),
                "ProposalsMade": "proposals_made",
            },
        )


    def _treaty_reached(self) -> bool:
        """Return True when at least 2/3 of countries have accepted."""
        agents = list(self.agents)
        if not agents:
            return False
        accepted = sum(1 for a in agents if getattr(a, "accepted_treaty", False))
        return accepted >= len(agents) * 2 / 3

    def _average_pledge(self) -> float:
        """Mean reduction pledge across all countries (percent)."""
        agents = list(self.agents)
        if not agents:
            return 0.0
        return sum(getattr(a, "current_pledge", 0.0) for a in agents) / len(agents)

    def _largest_coalition(self) -> int:
        """Size (including self) of the largest active coalition."""
        if not self.agents:
            return 0
        return max(
            len(getattr(a, "coalition_members", [])) + 1 for a in self.agents
        )


    def step(self):
        self.datacollector.collect(self)
        rprint(
            f"\n[bold cyan]- Climate Summit  Round {self.steps} "
            f"[/bold cyan]"
        )
        self.agents.shuffle_do("step")

        avg = self._average_pledge()
        treaty = self._treaty_reached()
        rprint(
            f"[bold green]  End of round {self.steps}: "
            f"avg_pledge={avg:.1f}%  "
            f"total_proposals={self.total_proposals}  "
            f"treaty_reached={treaty}[/bold green]"
        )


if __name__ == "__main__":
    """
    Run without visualization:
        cd examples/climate_negotiation
        python -m climate_negotiation.model
    """
    from mesa_llm.reasoning.react import ReActReasoning

    m = ClimateNegotiationModel(
        reasoning=ReActReasoning,
        llm_model="gemini/gemini-2.0-flash",
        rng=42,
    )
    for _ in range(5):
        m.step()
        if m._treaty_reached():
            rprint("[bold yellow]  *** Treaty consensus reached! ***[/bold yellow]")
            break
