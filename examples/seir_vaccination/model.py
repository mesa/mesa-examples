from agents import GovernmentAgent, PersonAgent, State
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.discrete_space import OrthogonalMooreGrid


class SEIRModel(Model):
    """
    SEIR Epidemic Model with Vaccination Policy.

    Models population-level disease spreading on a grid.
    A GovernmentAgent monitors infection rates and triggers
    vaccination campaigns when a threshold is crossed.

    Activation order (explicit, Mesa 3.x style):
        1. PersonAgents step (spreading, progression)
        2. GovernmentAgent steps (monitors and responds)
    """

    def __init__(
        self,
        width=30,
        height=30,
        initial_infected=5,
        transmission_rate=0.3,
        incubation_period=3,
        infection_duration=7,
        vaccination_threshold=0.1,
        vaccination_rate=0.05,
    ):
        super().__init__()

        self.width = width
        self.height = height
        self.initial_infected = initial_infected
        self.transmission_rate = transmission_rate
        self.incubation_period = incubation_period
        self.infection_duration = infection_duration
        self.vaccination_threshold = vaccination_threshold
        self.vaccination_rate = vaccination_rate

        # Grid setup — Mesa 3.x Cell API
        self.grid = OrthogonalMooreGrid((width, height), torus=False, capacity=1)

        # Place one person per cell
        for cell in self.grid.all_cells:
            person = PersonAgent(self, state=State.SUSCEPTIBLE)
            person.cell = cell

        # Seed initial infections
        initial_infected_agents = self.random.sample(
            list(self.agents_by_type[PersonAgent]), initial_infected
        )
        for agent in initial_infected_agents:
            agent.state = State.INFECTED

        # Government meta-agent (not placed on grid)
        self.government = GovernmentAgent(self)

        self.datacollector = DataCollector(
            model_reporters={
                "Susceptible": lambda m: sum(
                    1
                    for a in m.agents_by_type[PersonAgent]
                    if a.state == State.SUSCEPTIBLE
                ),
                "Exposed": lambda m: sum(
                    1 for a in m.agents_by_type[PersonAgent] if a.state == State.EXPOSED
                ),
                "Infected": lambda m: sum(
                    1
                    for a in m.agents_by_type[PersonAgent]
                    if a.state == State.INFECTED
                ),
                "Recovered": lambda m: sum(
                    1
                    for a in m.agents_by_type[PersonAgent]
                    if a.state == State.RECOVERED
                ),
                "Vaccination Active": lambda m: int(m.government.vaccination_active),
            }
        )

        self.datacollector.collect(self)
        self.running = True

    def step(self):
        # 1. All people act first — random activation
        self.agents_by_type[PersonAgent].shuffle_do("step")

        # 2. Government monitors and responds
        self.government.step()

        self.datacollector.collect(self)
