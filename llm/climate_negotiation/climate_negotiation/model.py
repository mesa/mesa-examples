import logging
import os
from mesa.datacollection import DataCollector
from mesa.model import Model
from rich import print as rprint

from .agents import CountryAgent
from mesa_llm.reasoning.react import ReActReasoning
from mesa_llm.reasoning.reasoning import Reasoning

_log_path = os.environ.get("CLIMATE_LOG_FILE", "climate_negotiation.log")
_file_handler = logging.FileHandler(_log_path, mode="w", encoding="utf-8")
_file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))

sim_logger = logging.getLogger("climate_negotiation")
sim_logger.setLevel(logging.DEBUG)
sim_logger.addHandler(_file_handler)
sim_logger.propagate = False

COUNTRIES: list[dict] = [
    {
        "country_name": "USA",
        "emissions_per_capita": 14.0,
        "gdp_per_capita": 76_000,
        "development_status": "developed",
        "system_prompt": (
            "You are the USA's chief climate negotiator. "
            "The USA is the largest historical emitter with a $76k GDP per capita. "
            "You support climate action but insist all major economies — especially "
            "China and India — commit to comparable reductions. You prefer "
            "market-based mechanisms and oppose unilateral economic disadvantages."
        ),
    },
    {
        "country_name": "EU",
        "emissions_per_capita": 6.0,
        "gdp_per_capita": 37_000,
        "development_status": "developed",
        "system_prompt": (
            "You are the EU's chief climate negotiator. "
            "The EU targets a 55% reduction by 2030 (Fit for 55) and leads global climate ambition. "
            "You push for legally binding targets for all developed nations and "
            "substantial financial support for developing nations. "
            "Actively build coalitions with high-ambition partners."
        ),
    },
    {
        "country_name": "China",
        "emissions_per_capita": 8.0,
        "gdp_per_capita": 12_700,
        "development_status": "developing",
        "system_prompt": (
            "You are China's chief climate negotiator. "
            "China is the world's largest current emitter but still a developing "
            "economy at $12.7k GDP per capita. You argue that developed nations caused "
            "most historical emissions and must bear greater financial burdens. "
            "You support long-term goals but resist targets that constrain development "
            "without adequate technology transfer and green finance from rich countries."
        ),
    },
    {
        "country_name": "India",
        "emissions_per_capita": 2.0,
        "gdp_per_capita": 2_500,
        "development_status": "developing",
        "system_prompt": (
            "You are India's chief climate negotiator. "
            "India has very low per-capita emissions (2.0 tCO2) and a $2.5k GDP. "
            "You firmly defend common but differentiated responsibilities. "
            "India needs fossil fuel access to develop. You support renewables "
            "but reject targets that deny energy access to 1.4 billion people. "
            "Form strong coalitions with other developing nations."
        ),
    },
    {
        "country_name": "Brazil",
        "emissions_per_capita": 2.8,
        "gdp_per_capita": 10_400,
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
        "emissions_per_capita": 12.5,
        "gdp_per_capita": 15_000,
        "development_status": "developed",
        "system_prompt": (
            "You are Russia's chief climate negotiator. "
            "Russia is a major fossil fuel exporter with 12.5 tCO2 per capita. "
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
        reasoning: type[Reasoning] = ReActReasoning,
        llm_model: str = "gemini/gemini-2.0-flash",
        rng: int = 42,
    ):
        super().__init__(rng=rng)

        self.total_proposals: int = 0
        self.total_acceptances: int = 0

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
        round_num = self.steps
        rprint(
            f"\n[bold cyan]- Climate Summit  Round {round_num} "
            f"[/bold cyan]"
        )
        sim_logger.info("=" * 60)
        sim_logger.info(f"ROUND {round_num} START")
        sim_logger.info("=" * 60)

        # Log each agent's state at the start of the round
        for a in self.agents:
            sim_logger.debug(
                f"  Agent {a.unique_id} ({getattr(a, 'country_name', '?')}): "
                f"pledge={getattr(a, 'current_pledge', 0):.1f}%  "
                f"accepted={getattr(a, 'accepted_treaty', False)}  "
                f"coalition={getattr(a, 'coalition_members', [])}"
            )

        self.agents.shuffle_do("step")

        avg = self._average_pledge()
        treaty = self._treaty_reached()
        rprint(
            f"[bold green]  End of round {round_num}: "
            f"avg_pledge={avg:.1f}%  "
            f"total_proposals={self.total_proposals}  "
            f"treaty_reached={treaty}[/bold green]"
        )
        sim_logger.info(
            f"ROUND {round_num} END | "
            f"avg_pledge={avg:.1f}%  "
            f"total_proposals={self.total_proposals}  "
            f"total_acceptances={self.total_acceptances}  "
            f"treaty_reached={treaty}"
        )
        # Log final state of each agent after the round
        for a in self.agents:
            sim_logger.info(
                f"  [{getattr(a, 'country_name', a.unique_id)}] "
                f"pledge={getattr(a, 'current_pledge', 0):.1f}%  "
                f"accepted={getattr(a, 'accepted_treaty', False)}  "
                f"proposals_made={getattr(a, 'proposals_made', 0)}  "
                f"coalition={getattr(a, 'coalition_members', [])}"
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
