import mesa
from mesa import Model
from mesa.discrete_space import OrthogonalMooreGrid, OrthogonalVonNeumannGrid

from .agent import Person


class RumorMillModel(Model):
    """
    Model simulating rumor spread through a population on a grid.
    """

    def __init__(
        self,
        width=10,
        height=10,
        know_rumor_ratio=0.01,
        rumor_spread_chance=0.5,
        eight_neightborhood=False,
        seed=None,
    ):
        """
        Initialize the Rumor Mill model.

        Args:
            width: Grid width
            height: Grid height
            know_rumor_ratio: Initial proportion of agents who know the rumor (0.0-1.0)
            rumor_spread_chance: Probability of successful rumor transmission (0.0-1.0)
            eight_neightborhood: If True, use Moore (8-neighbor), else Von Neumann (4-neighbor)
            seed: Random seed for reproducibility
        """
        super().__init__(seed=seed)
        self.number_of_agents = width * height
        self.know_rumor_ratio = know_rumor_ratio
        self.rumor_spread_chance = rumor_spread_chance

        # Create grid with appropriate neighborhood type
        if eight_neightborhood:
            self.grid = OrthogonalMooreGrid(
                (width, height), random=self.random
            )  # 8 neighbors
        else:
            self.grid = OrthogonalVonNeumannGrid(
                (width, height), random=self.random
            )  # 4 neighbors

        # Determine initial rumor knowers and assign colors
        num_initial_rumor_knowers = int(self.number_of_agents * self.know_rumor_ratio)
        colors = ["red"] * num_initial_rumor_knowers + ["blue"] * (
            self.number_of_agents - num_initial_rumor_knowers
        )
        self.random.shuffle(colors)  # Randomize which agents start with rumor

        # Create all agents and place them on grid cells
        Person.create_agents(
            self,
            self.number_of_agents,
            list(self.grid.all_cells.cells),
            rumor_spread_chance=self.rumor_spread_chance,
            color=colors,
        )

        # Set initial rumor knowledge for agents with red color
        for agent in self.agents:
            if agent.color == "red":
                agent.knows_rumor = True
                agent.times_heard = 1
                agent.newly_learned = True  # They learned it initially

        # Set up data collection
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Percentage_Knowing_Rumor": self.compute_percentage_knowing_rumor,
                "Times_Heard_Rumor_Per_Step": self.compute_new_rumor_times_heard,
                "New_People_Knowing_Rumor": self.compute_new_people_ratio_knowing_rumor,
            }
        )
        self.datacollector.collect(self)

    def step(self):
        """Execute one step of the model: all agents act, then collect data."""
        # Reset per-step counters for all agents at start of step
        for agent in self.agents:
            agent.newly_learned = False
            agent.times_heard_this_step = 0
        self.agents.shuffle_do("step")  # Activate all agents in random order
        self.datacollector.collect(self)  # Collect data for this step

    def compute_percentage_knowing_rumor(self):
        """Calculate percentage of agents who know the rumor."""
        agents_knowing = sum(1 for agent in self.agents if agent.knows_rumor)
        return (
            (agents_knowing / self.number_of_agents) * 100
            if self.number_of_agents > 0
            else 0
        )

    def compute_new_rumor_times_heard(self):
        """Calculate total times rumor was heard this step (whether learned or not)."""
        total_heard_this_step = sum(
            agent.times_heard_this_step for agent in self.agents
        )
        return total_heard_this_step

    def compute_new_people_ratio_knowing_rumor(self):
        """Calculate percentage of new people who learned the rumor this step."""
        new_knowers = sum(1 for agent in self.agents if agent.newly_learned)
        return (
            (new_knowers / self.number_of_agents) * 100
            if self.number_of_agents > 0
            else 0
        )
