import mesa
from mesa.discrete_space import HexGrid

from .agent import Ant


class AntForaging(mesa.Model):
    """
    Au ant foraging model on a Hexagonal Grid.

    This demonstrates the power of PropertyLayers for efficient environmental
    simulation (pheromones) combined with complex agent movement.
    """

    def __init__(
        self,
        width=30,
        height=30,
        num_ants=50,
        evaporation_rate=0.05,
        diffusion_rate=0.2,
    ):
        super().__init__()
        self.evaporation_rate = evaporation_rate
        self.diffusion_rate = diffusion_rate

        # We use a HexGrid with torus wrapping for a seamless infinite world feel
        self.grid = HexGrid((width, height), torus=True, random=self.random)

        # Environment Setup using PropertyLayers
        # Use numpy arrays for efficient O(1) access

        # 1. Food Pheromone (Red): Leads ants to food.
        self.grid.create_property_layer(
            "pheromone_food", default_value=0.0, dtype=float
        )

        # 2. Home Pheromone (Blue): Leads ants home.
        self.grid.create_property_layer(
            "pheromone_home", default_value=0.0, dtype=float
        )

        # 3. Food Source (Green): Food location quantities.
        self.grid.create_property_layer("food", default_value=0, dtype=int)

        # 4. Obstacles (Black).
        self.grid.create_property_layer("obstacles", default_value=0, dtype=int)

        # 5. Home (White): Nest location.
        self.grid.create_property_layer("home", default_value=0, dtype=int)

        self._init_environment()
        self._init_agents(num_ants)

    def _init_environment(self):
        """Setup initial food clusters and the central nest."""
        # Create the Nest in the center
        center = (self.grid.width // 2, self.grid.height // 2)
        # Spike the 'home' pheromone at the nest so ants can find it initially
        self.grid.pheromone_home.data[center] = 1.0
        # Mark the home location
        self.grid.home.data[center] = 1

        # Scatter some Food Sources
        # Create 3 big clusters of food
        for _ in range(3):
            # Pick a random spot
            cx = self.random.randint(0, self.grid.width - 1)
            cy = self.random.randint(0, self.grid.height - 1)

            # Create a blob around it
            cluster_center = (cx, cy)
            blob = self.grid[cluster_center].get_neighborhood(
                radius=3, include_center=True
            )
            for cell in blob:
                # Give each cell plenty of food
                cell.food = self.random.randint(50, 100)

    def _init_agents(self, num_ants):
        """Spawn our ants at the nest."""
        center = (self.grid.width // 2, self.grid.height // 2)
        center_cell = self.grid[center]

        for _ in range(num_ants):
            ant = Ant(self)
            # Add agent to the cell (spatial placement)
            ant.cell = center_cell

    def step(self):
        """Advance the model by one step."""
        # 1. Environment Dynamics
        # Pheromones diffuse and evaporate.
        self._update_pheromone_layer("pheromone_food")
        self._update_pheromone_layer("pheromone_home")

        # 2. Agent Dynamics
        self.agents.shuffle_do("step")

    def _update_pheromone_layer(self, layer_name):
        """
        Apply evaporation to a pheromone layer.
        """
        layer = getattr(self.grid, layer_name)

        # Evaporation
        np_layer = layer.data
        np_layer *= 1.0 - self.evaporation_rate

        # Clamp to 0 to prevent negative values
        np_layer[np_layer < 0.001] = 0
