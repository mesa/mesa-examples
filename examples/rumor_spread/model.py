from mesa import Model
from mesa.datacollection import DataCollector
from mesa.discrete_space import CellAgent
from mesa.discrete_space.grid import OrthogonalMooreGrid


class RumorAgent(CellAgent):
    """A grid-based agent that may or may not know the rumor."""

    def __init__(self, model, cell=None, has_rumor=False):
        super().__init__(model)
        if cell is not None:
            self.cell = cell
        self.has_rumor = has_rumor
        self.resistance = self.random.random()

    def step(self):
        """Spread the rumor to neighboring agents probabilistically."""
        if not self.has_rumor:
            return

        for neighbor_cell in self.cell.neighborhood:
            for agent in neighbor_cell.agents:
                if not agent.has_rumor:
                    spread_probability = self.model.infection_strength * (1 - agent.resistance) * 0.3
                    if self.random.random() < spread_probability:
                        agent.has_rumor = True

        # Recovery (forget rumor)
        if self.random.random() < self.model.recovery_rate:
            self.has_rumor = False


class RumorModel(Model):
    """A simple rumor diffusion model on a 2D toroidal grid."""

    def __init__(
        self,
        width=20,
        height=20,
        initial_spreaders=2,
        infection_strength=0.2,
        recovery_rate=0.05,
        rng=None,
    ):
        super().__init__(rng=rng)

        self.width = width
        self.height = height
        self.initial_spreaders = initial_spreaders
        self.infection_strength = infection_strength
        self.recovery_rate = recovery_rate

        self.grid = OrthogonalMooreGrid(
            (width, height),
            torus=True,
            capacity=1,
            random=self.random,
        )

        self.datacollector = DataCollector(
            model_reporters={
                "Informed": lambda m: sum(agent.has_rumor for agent in m.agents),
            }
        )

        self._initialize_agents()
        self.running = True
        self.datacollector.collect(self)

    def _initialize_agents(self):
        """Create and place agents on the grid."""
        all_coords = [(x, y) for x in range(self.width) for y in range(self.height)]
        initial_informed = set(self.random.sample(all_coords, self.initial_spreaders))

        for x, y in all_coords:
            has_rumor = (x, y) in initial_informed
            cell = self.grid[(x, y)]
            agent = RumorAgent(self, cell=cell, has_rumor=has_rumor)
            self.agents.add(agent)

    def step(self):
        """Advance the model by one step."""
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)