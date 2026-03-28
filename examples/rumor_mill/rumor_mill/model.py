import mesa
from mesa import Model
from mesa.discrete_space import OrthogonalMooreGrid, OrthogonalVonNeumannGrid
from rumor_mill.agent import Person, Debunker

class RumorMillModel(Model):
    """
    Rumor Mill model — extended.

    Extensions over the base model:
    - Skepticism attribute per agent reducing effective spread chance
    - Forgetting mechanic allowing agents to lose the rumor over time
    - Debunker agent subclass that actively counters the rumor
    - New metrics tracking forgotten agents and debunker effectiveness
    """

    def __init__(
        self,
        width=10,
        height=10,
        know_rumor_ratio=0.01,
        rumor_spread_chance=0.5,
        eight_neightborhood=False,
        skepticism_mean=0.0,
        forget_chance=0.0,
        fraction_debunkers=0.0,
        rng=None,
    ):
        super().__init__(rng=rng)
        self.number_of_agents = width * height
        self.know_rumor_ratio = know_rumor_ratio
        self.rumor_spread_chance = rumor_spread_chance
        self.skepticism_mean = skepticism_mean
        self.forget_chance = forget_chance
        self.fraction_debunkers = fraction_debunkers

        if eight_neightborhood:
            self.grid = OrthogonalMooreGrid((width, height), random=self.random)
        else:
            self.grid = OrthogonalVonNeumannGrid((width, height), random=self.random)

        num_initial_rumor_knowers = int(self.number_of_agents * self.know_rumor_ratio)
        num_debunkers = int(self.number_of_agents * self.fraction_debunkers)

        all_cells = list(self.grid.all_cells.cells)
        self.random.shuffle(all_cells)

        rumor_cells = set(all_cells[:num_initial_rumor_knowers])
        debunker_cells = set(all_cells[num_initial_rumor_knowers:num_initial_rumor_knowers + num_debunkers])

        for cell in all_cells:
            skepticism = max(0.0, min(1.0, self.random.gauss(skepticism_mean, 0.1)))
            if cell in rumor_cells:
                agent = Person(self, cell, rumor_spread_chance, skepticism, forget_chance, "red")
                agent.knows_rumor = True
                agent.times_heard = 1
                agent.newly_learned = True
            elif cell in debunker_cells:
                agent = Debunker(self, cell, rumor_spread_chance, skepticism, forget_chance, "green")
            else:
                agent = Person(self, cell, rumor_spread_chance, skepticism, forget_chance, "blue")
            self.agents.add(agent)

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Percentage_Knowing_Rumor": self.compute_percentage_knowing_rumor,
                "Times_Heard_Rumor_Per_Step": self.compute_new_rumor_times_heard,
                "New_People_Knowing_Rumor": self.compute_new_people_ratio_knowing_rumor,
                "Percentage_Forgotten": self.compute_percentage_forgotten,
                "Debunker_Effectiveness": self.compute_debunker_effectiveness,
            }
        )
        self.datacollector.collect(self)

    def step(self):
        for agent in self.agents:
            agent.newly_learned = False
            agent.newly_forgotten = False
            agent.times_heard_this_step = 0
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)

    def compute_percentage_knowing_rumor(self):
        agents_knowing = sum(1 for a in self.agents if a.knows_rumor)
        return (agents_knowing / self.number_of_agents) * 100 if self.number_of_agents > 0 else 0

    def compute_new_rumor_times_heard(self):
        return sum(a.times_heard_this_step for a in self.agents)

    def compute_new_people_ratio_knowing_rumor(self):
        new_knowers = sum(1 for a in self.agents if a.newly_learned)
        return (new_knowers / self.number_of_agents) * 100 if self.number_of_agents > 0 else 0

    def compute_percentage_forgotten(self):
        forgotten = sum(1 for a in self.agents if a.newly_forgotten)
        return (forgotten / self.number_of_agents) * 100 if self.number_of_agents > 0 else 0

    def compute_debunker_effectiveness(self):
        debunkers = [a for a in self.agents if hasattr(a, "agent_type") and a.agent_type == "debunker"]
        if not debunkers:
            return 0
        successes = sum(1 for a in self.agents if a.newly_forgotten and not hasattr(a, "agent_type"))
        return (successes / len(debunkers)) * 100