import mesa
from mesa.discrete_space import OrthogonalMooreGrid, CellAgent


class ForagerAgent(CellAgent):
    """
    A foraging agent with state-based behavior.

    States
    ------
    searching : moves and tries to collect resources
    resting   : recovers energy
    """

    def __init__(self, model, energy=50.0):
        super().__init__(model)
        self.energy = energy
        self.state = "searching"

    def step(self):
        # Update state
        if self.state == "searching" and self.energy <= 20:
            self.state = "resting"
        elif self.state == "resting" and self.energy >= 80:
            self.state = "searching"

        # Always drain energy
        self.energy = max(0, self.energy - 2.0)

        # State-specific behavior
        if self.state == "searching":
            self._move()
            self._forage()
        elif self.state == "resting":
            self._rest()

    def _move(self):
        neighbors = self.cell.connections.values()
        if neighbors:
            self.cell = self.random.choice(list(neighbors))

    def _forage(self):
        pos = (self.cell.coordinate[0], self.cell.coordinate[1])
        if pos in self.model.resources and self.model.resources[pos] > 0:
            collected = min(15.0, self.model.resources[pos])
            self.model.resources[pos] -= collected
            self.energy = min(100, self.energy + collected)

    def _rest(self):
        self.energy = min(100, self.energy + 8.0)


class ForagerModel(mesa.Model):
    """
    Foraging simulation demonstrating modular agent behavior.

    Parameters
    ----------
    n_agents         : number of forager agents
    width, height    : grid dimensions
    resource_density : fraction of cells containing resources
    """

    def __init__(
        self,
        n_agents=10,
        width=20,
        height=20,
        resource_density=0.3,
    ):
        super().__init__()
        self.grid = OrthogonalMooreGrid(
            (width, height), torus=True, capacity=None
        )

        # Place resources
        self.resources = {}
        for cell in self.grid.all_cells:
            if self.random.random() < resource_density:
                self.resources[cell.coordinate] = 20.0

        # Create agents
        for _ in range(n_agents):
            agent = ForagerAgent(self)
            cell = self.random.choice(list(self.grid.all_cells))
            agent.cell = cell

        self.datacollector = mesa.DataCollector(
            agent_reporters={
                "energy": "energy",
                "state": "state",
            },
            model_reporters={
                "searching": lambda m: sum(
                    1 for a in m.agents if a.state == "searching"
                ),
                "resting": lambda m: sum(
                    1 for a in m.agents if a.state == "resting"
                ),
                "total_resources": lambda m: sum(m.resources.values()),
            },
        )

    def step(self):
        self.datacollector.collect(self)
        self.agents.shuffle_do("step")
        for pos in self.resources:
            self.resources[pos] = min(20.0, self.resources[pos] + 0.2)
