from enum import Enum

from mesa.discrete_space import CellAgent


class State(Enum):
    SUSCEPTIBLE = "S"
    EXPOSED = "E"
    INFECTED = "I"
    RECOVERED = "R"


class PersonAgent(CellAgent):
    """
    Represents a person in the population.

    States:
        SUSCEPTIBLE: healthy, can get infected
        EXPOSED: infected but not yet contagious
        INFECTED: contagious, can spread to neighbors
        RECOVERED: immune, cannot be infected again
    """

    def __init__(self, model, state=State.SUSCEPTIBLE):
        super().__init__(model)
        self.state = state
        self.days_exposed = 0
        self.days_infected = 0

    def step(self):
        if self.state == State.SUSCEPTIBLE:
            self._try_get_exposed()
        elif self.state == State.EXPOSED:
            self._progress_to_infected()
        elif self.state == State.INFECTED:
            self._progress_to_recovered()

    def _try_get_exposed(self):
        """Check neighbors — if any are Infected, maybe become Exposed."""
        for neighbor_cell in self.cell.connections.values():
            for neighbor in neighbor_cell.agents:
                if (
                    isinstance(neighbor, PersonAgent)
                    and neighbor.state == State.INFECTED
                    and self.random.random() < self.model.transmission_rate
                ):
                    self.state = State.EXPOSED
                    return

    def _progress_to_infected(self):
        """After incubation period, become Infected."""
        self.days_exposed += 1
        if self.days_exposed >= self.model.incubation_period:
            self.state = State.INFECTED
            self.days_exposed = 0

    def _progress_to_recovered(self):
        """After infection period, recover."""
        self.days_infected += 1
        if self.days_infected >= self.model.infection_duration:
            self.state = State.RECOVERED
            self.days_infected = 0

    def vaccinate(self):
        """Directly move Susceptible person to Recovered via vaccination."""
        if self.state == State.SUSCEPTIBLE:
            self.state = State.RECOVERED


class GovernmentAgent(CellAgent):
    """
    Meta-agent representing the government.

    Monitors infection rate each step and triggers
    vaccination campaigns when threshold is crossed.
    """

    def __init__(self, model):
        super().__init__(model)
        self.vaccination_active = False

    def step(self):
        self._monitor_and_respond()

    def _monitor_and_respond(self):
        """Check infection rate and trigger vaccination if needed."""
        total = len(self.model.agents_by_type[PersonAgent])
        if total == 0:
            return

        infected_count = sum(
            1
            for a in self.model.agents_by_type[PersonAgent]
            if a.state == State.INFECTED
        )
        infection_rate = infected_count / total

        if infection_rate >= self.model.vaccination_threshold:
            self.vaccination_active = True
            self._run_vaccination_campaign()
        else:
            self.vaccination_active = False

    def _run_vaccination_campaign(self):
        """Vaccinate a fraction of susceptible people."""
        susceptible = [
            a
            for a in self.model.agents_by_type[PersonAgent]
            if a.state == State.SUSCEPTIBLE
        ]
        n_to_vaccinate = int(len(susceptible) * self.model.vaccination_rate)
        targets = self.random.sample(susceptible, min(n_to_vaccinate, len(susceptible)))
        for person in targets:
            person.vaccinate()