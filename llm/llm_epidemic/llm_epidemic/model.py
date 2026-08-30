from mesa import Model
from mesa.datacollection import DataCollector
from mesa.discrete_space import OrthogonalMooreGrid
from mesa_llm.memory.st_memory import ShortTermMemory

from .agent import EpidemicAgent


class EpidemicModel(Model):
    """
    An epidemic simulation where agents use LLM Chain-of-Thought reasoning
    to decide their behavior during an outbreak.

    Unlike classical SIR models with fixed transition probabilities, agents
    here reason about their situation — weighing personal risk, community
    responsibility, and observed neighbor states — to decide whether to
    isolate, move freely, or seek treatment.

    This produces emergent epidemic curves that reflect reasoning-driven
    behavioral responses rather than purely stochastic transitions.

    Attributes:
        num_agents (int): Total number of agents in the simulation.
        initial_infected (int): Number of agents infected at the start.
        grid (OrthogonalMooreGrid): The spatial grid agents inhabit.
        susceptible_count (int): Current number of susceptible agents.
        infected_count (int): Current number of infected agents.
        recovered_count (int): Current number of recovered agents.

    Reference:
        Kermack, W. O., & McKendrick, A. G. (1927). A contribution to the
        mathematical theory of epidemics. Proceedings of the Royal Society
        of London. Series A, 115(772), 700-721.
    """

    def __init__(
        self,
        num_agents: int = 20,
        initial_infected: int = 3,
        grid_size: int = 10,
        llm_model: str = "gemini/gemini-2.0-flash",
    ):
        super().__init__()

        self.num_agents = num_agents
        self.initial_infected = initial_infected
        self.grid = OrthogonalMooreGrid(
            (grid_size, grid_size), torus=False, random=self.random
        )

        self.susceptible_count = num_agents - initial_infected
        self.infected_count = initial_infected
        self.recovered_count = 0

        # Create agents
        all_cells = list(self.grid.all_cells)
        self.random.shuffle(all_cells)

        for i in range(num_agents):
            health_state = "infected" if i < initial_infected else "susceptible"
            agent = EpidemicAgent(model=self, health_state=health_state)
            agent.memory = ShortTermMemory(agent=agent, n=5, display=False)
            agent._update_internal_state()

            # Place agent on grid
            cell = all_cells[i % len(all_cells)]
            cell.add_agent(agent)
            agent.cell = cell
            agent.pos = cell.coordinate

        # Data collection
        self.datacollector = DataCollector(
            model_reporters={
                "susceptible_count": "susceptible_count",
                "infected_count": "infected_count",
                "recovered_count": "recovered_count",
            }
        )
        self.datacollector.collect(self)

    def _update_counts(self) -> None:
        """Recount agent health states after each step."""
        self.susceptible_count = sum(
            1
            for a in self.agents
            if hasattr(a, "health_state") and a.health_state == "susceptible"
        )
        self.infected_count = sum(
            1
            for a in self.agents
            if hasattr(a, "health_state") and a.health_state == "infected"
        )
        self.recovered_count = sum(
            1
            for a in self.agents
            if hasattr(a, "health_state") and a.health_state == "recovered"
        )

    def step(self) -> None:
        """Advance the model by one step."""
        for agent in self.agents:
            if hasattr(agent, "_update_internal_state"):
                agent._update_internal_state()
                agent._update_health()

        self._update_counts()
        self.datacollector.collect(self)
