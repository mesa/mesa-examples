import mesa
from mesa.discrete_space import OrthogonalMooreGrid

from .agents import Beneficiary, Truck


class HumanitarianModel(mesa.Model):
    """
    The central environment for the Needs-Based Architecture simulation.

    This model manages:
    1. A grid space where agents interact.
    2. A scheduler to activate agents in random order each step.
    3. Data collection to track global statistics (e.g., average urgency).

    Attributes:
        num_beneficiaries (int): Number of civilian agents with needs.
        num_trucks (int): Number of aid trucks.
        grid (mesa.discrete_space.OrthogonalMooreGrid): Spatial environment.
    """

    def __init__(
        self,
        num_beneficiaries=30,
        num_trucks=3,
        width=20,
        height=20,
        seed=None,
        critical_days_threshold=5,
    ):
        """
        Create a new Humanitarian model with the given parameters.

        Args:
            num_beneficiaries (int): Number of beneficiaries to create.
            num_trucks (int): Number of trucks to create.
            width (int): Width of the grid.
            height (int): Height of the grid.
            seed (int, optional): Random seed for reproducibility.
            critical_days_threshold (int): Days before death when critical.
        """
        super().__init__(seed=seed)

        self.num_beneficiaries = num_beneficiaries
        self.num_trucks = num_trucks
        self.critical_days_threshold = critical_days_threshold

        # 1. Create Grid
        self.grid = OrthogonalMooreGrid(
            (width, height), torus=False, random=self.random, capacity=None
        )

        # 2. Setup Property Layer for the Depot
        self.grid.create_property_layer("is_depot", default_value=False, dtype=bool)
        self.grid[(0, 0)].is_depot = True  # Set the depot location

        # 3. Create Agents
        self.create_agents()

        # 4. Setup Data Collection
        # We use model.grid.agents to ensure we only count active agents
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Avg Urgency": self.get_average_urgency,
                "Deaths": self.get_total_deaths,
                "Critical Count": self.get_critical_count,
            }
        )
        self.running = True

    def create_agents(self):
        """
        Create and place agents using high-level grid methods.
        """
        random_cells = self.random.choices(
            list(self.grid.all_cells), k=self.num_beneficiaries
        )

        Beneficiary.create_agents(
            self,
            n=self.num_beneficiaries,
            cell=random_cells,
            critical_days_threshold=self.critical_days_threshold,
        )

        depot_cell = self.grid[(0, 0)]

        Truck.create_agents(
            self,
            n=self.num_trucks,
            cell=depot_cell,
        )

    def step(self):
        """
        Advance the model by one step.

        Lifecycle:
        1. Collect Data: Record current model stats (e.g. Average Urgency).
        2. Agent Steps: Activate all agents in random order.
        """
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)

    @staticmethod
    def get_average_urgency(model):
        """
        Helper for data collection: Calculates the average urgency of all beneficiaries.

        Args:
            model (HumanitarianModel): The model instance.

        Returns:
            float: The average urgency (water + food) or 0 if no beneficiaries.
        """
        beneficiaries = [a for a in model.grid.agents if isinstance(a, Beneficiary)]
        if not beneficiaries:
            return 0
        total = sum(a.water_urgency + a.food_urgency for a in beneficiaries)
        return total / len(beneficiaries)

    @staticmethod
    def get_total_deaths(model):
        """Measures System Failure (Cumulative)"""
        current_count = len(
            [a for a in model.grid.agents if isinstance(a, Beneficiary)]
        )
        return model.num_beneficiaries - current_count

    @staticmethod
    def get_critical_count(model):
        """Measures Immediate Danger"""
        # Adapted to use is_critical flag since state is 'seeking' or 'wandering'
        return sum(
            1 for a in model.grid.agents if isinstance(a, Beneficiary) and a.is_critical
        )
