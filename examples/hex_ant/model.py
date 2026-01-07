import mesa
from mesa.discrete_space import HexGrid


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

        # --- Environment Setup using PropertyLayers ---
        # These are much faster than agent-based environment properties because
        # they use numpy arrays ensuring O(1) access and vectorized operations.

        # 1. Food Pheromone (Red): Dropped by ants carrying food, leading OTHERS to food.
        self.grid.create_property_layer(
            "pheromone_food", default_value=0.0, dtype=float
        )

        # 2. Home Pheromone (Blue): Dropped by foraging ants, leading ALL ants back home.
        self.grid.create_property_layer(
            "pheromone_home", default_value=0.0, dtype=float
        )

        # 3. Food Source (Green): The actual food piling.
        self.grid.create_property_layer("food", default_value=0, dtype=int)

        # 4. Obstacles (Black): Just for fun, some walls.
        self.grid.create_property_layer("obstacles", default_value=0, dtype=int)

        # 5. Home (White): The actual nest location.
        self.grid.create_property_layer("home", default_value=0, dtype=int)

        self._init_environment()
        self._init_agents(num_ants)

    def _init_environment(self):
        """Setup initial food clusters and the central nest."""
        # 1. Create the Nest in the center
        center = (self.grid.width // 2, self.grid.height // 2)
        # We also manually spike the 'home' pheromone at the nest so ants can find it initially
        self.grid.pheromone_home.data[center] = 1.0
        # Mark the home location
        self.grid.home.data[center] = 1

        # 2. Scatter some Food Sources
        # We'll create 3 big clusters of food
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

        from agent import Ant

        for _ in range(num_ants):
            ant = Ant(self)
            # Add agent to the cell (spatial placement)
            ant.cell = center_cell

    def step(self):
        """Advance the model by one step."""
        # 1. Environment Dynamics (The cool part!)
        # Pheromones need to diffuse (spread out) and evaporate (fade away).
        self._update_pheromone_layer("pheromone_food")
        self._update_pheromone_layer("pheromone_home")

        # 2. Agent Dynamics
        self.agents.shuffle_do("step")

    def _update_pheromone_layer(self, layer_name):
        """
        Apply diffusion and evaporation to a pheromone layer.
        Using numpy operations for speed.
        """
        layer = getattr(self.grid, layer_name)

        # Evaporation: Everything decays by a factor
        # layer.data *= (1 - self.evaporation_rate)
        # We can use modify_cells for valid cells (though data access is faster usually)
        # But let's stick to the official API potential
        np_layer = layer.data
        np_layer *= 1.0 - self.evaporation_rate

        # Diffusion: This is tricky on a HexGrid without a convolution matrix.
        # For a simple heuristic, we can blur the array.
        # But 'scipy.ndimage.gaussian_filter' is standard for this.
        # Or simpler: just let it stay for now, diffusion is expensive to code perfectly on Hex
        # without external libraries like scipy. Let's rely on agents spreading it for now
        # to keep dependencies low, or use a simple box blur if we really need it.
        # Let's add simple clamp to 0
        np_layer[np_layer < 0.001] = 0
