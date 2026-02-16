"""This file was copied over from the original Schelling mesa example."""

import mesa
from mesa.discrete_space import CellAgent, OrthogonalMooreGrid


class SchellingAgent(CellAgent):
    """Schelling segregation agent"""

    def __init__(self, model, agent_type):
        """Create a new Schelling agent.

        Args:
           x, y: Agent initial location.
           agent_type: Indicator for the agent's type (minority=1, majority=0)
        """
        super().__init__(model)
        self.type = agent_type

    def step(self):
        similar = 0
        for agent in self.cell.get_neighborhood(radius=self.model.radius).agents:
            if agent.type == self.type:
                similar += 1

        # If unhappy, move:
        if similar < self.model.homophily:
            self.cell = self.model.grid.select_random_empty_cell()
        else:
            self.model.happy += 1


class Schelling(mesa.Model):
    """Model class for the Schelling segregation model."""

    def __init__(
        self,
        height=20,
        width=20,
        homophily=3,
        radius=1,
        density=0.8,
        minority_pc=0.3,
        rng=None,
    ):
        """Create a new Schelling model.

        Args:
            width, height: Size of the space.
            density: Initial Chance for a cell to populated
            minority_pc: Chances for an agent to be in minority class
            homophily: Minimum number of agents of same class needed to be happy
            radius: Search radius for checking similarity
            rng: Seed for Reproducibility
        """
        super().__init__(rng=rng)
        self.height = height
        self.width = width
        self.density = density
        self.minority_pc = minority_pc
        self.homophily = homophily
        self.radius = radius

        self.grid = OrthogonalMooreGrid((width, height), torus=True, random=self.random)

        self.happy = 0
        self.datacollector = mesa.DataCollector(
            model_reporters={"happy": "happy"},  # Model-level count of happy agents
        )

        # Set up agents
        # We use a grid iterator that returns
        # the coordinates of a cell as well as
        # its contents. (coord_iter)
        for cell in self.grid.all_cells:
            if self.random.random() < self.density:
                agent_type = 1 if self.random.random() < self.minority_pc else 0
                agent = SchellingAgent(self, agent_type)
                agent.cell = cell

        self.datacollector.collect(self)

    def step(self):
        """Run one step of the model."""
        self.happy = 0  # Reset counter of happy agents
        self.agents.shuffle_do("step")

        self.datacollector.collect(self)

        if self.happy == len(self.agents):
            self.running = False
