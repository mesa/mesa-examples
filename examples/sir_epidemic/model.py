"""SIR Epidemic Model.

A Susceptible-Infected-Recovered epidemic model demonstrating disease spread
on a 2D grid using Mesa's discrete space API. Agents move randomly, infected
agents can spread the disease to susceptible neighbors, and infected agents
recover after a set number of steps.
"""

import mesa
from mesa.discrete_space import CellAgent, OrthogonalMooreGrid


class Person(CellAgent):
    """An agent representing a person in the SIR model.

    Attributes:
        state: Current health state - "Susceptible", "Infected", or "Recovered".
        infection_timer: Number of steps since infection.
        recovery_time: Steps required to recover from infection.
    """

    def __init__(self, model, initial_state="Susceptible"):
        super().__init__(model)
        self.state = initial_state
        self.infection_timer = 0
        self.recovery_time = model.recovery_time

    def step(self):
        """Move randomly, spread infection, and check recovery."""
        # Move to a random neighboring cell
        neighborhood = self.cell.neighborhood
        self.cell = neighborhood.select_random_cell()

        # If infected, try to spread to susceptible neighbors
        if self.state == "Infected":
            for neighbor in self.cell.neighborhood.agents:
                if (
                    neighbor.state == "Susceptible"
                    and self.random.random() < self.model.infection_rate
                ):
                    neighbor.state = "Infected"

            # Check if agent should recover
            self.infection_timer += 1
            if self.infection_timer >= self.recovery_time:
                self.state = "Recovered"


class SIRModel(mesa.Model):
    """A simple SIR epidemic model.

    Args:
        num_agents: Total number of agents in the simulation.
        width: Width of the grid.
        height: Height of the grid.
        infection_rate: Probability of infection spreading per contact.
        recovery_time: Number of steps before an infected agent recovers.
        initial_infected: Number of agents initially infected.
        seed: Random seed for reproducibility.
    """

    def __init__(
        self,
        num_agents=100,
        width=20,
        height=20,
        infection_rate=0.3,
        recovery_time=10,
        initial_infected=3,
    ):
        super().__init__()
        self.infection_rate = infection_rate
        self.recovery_time = recovery_time

        # Create grid
        self.grid = OrthogonalMooreGrid((width, height), torus=True, random=self.random)

        # Create DataCollector
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Susceptible": lambda m: sum(
                    1 for a in m.agents if a.state == "Susceptible"
                ),
                "Infected": lambda m: sum(1 for a in m.agents if a.state == "Infected"),
                "Recovered": lambda m: sum(
                    1 for a in m.agents if a.state == "Recovered"
                ),
            }
        )

        # Create agents and place on random cells
        for _ in range(num_agents):
            agent = Person(self, initial_state="Susceptible")
            agent.cell = self.grid.all_cells.select_random_cell()

        # Infect initial agents
        infected_agents = self.random.sample(list(self.agents), initial_infected)
        for agent in infected_agents:
            agent.state = "Infected"

        self.datacollector.collect(self)

    def step(self):
        """Advance the model by one step."""
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)


if __name__ == "__main__":
    model = SIRModel()
    for _ in range(50):
        model.step()
    data = model.datacollector.get_model_vars_dataframe()
    print(data)
