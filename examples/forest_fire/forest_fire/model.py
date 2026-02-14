import math

import mesa
from mesa.discrete_space import OrthogonalMooreGrid

from .agent import TreeCell


class ForestFire(mesa.Model):
    """Simple Forest Fire model."""

    def __init__(
        self,
        width=100,
        height=100,
        density=0.65,
        seed=None,
        use_prob=False,
        p_spread=0.5,
        wind_enabled=False,
        wind_dir=0.0,
        wind_strength=1.0,
    ):
        """Create a new forest fire model.

        Args:
            width, height: The size of the grid to model
            density: What fraction of grid cells have a tree in them.
        """
        super().__init__(seed=seed)

        # for wind extended
        self.p_spread = p_spread if use_prob else None
        self.wind_enabled = wind_enabled
        self.wind_dir = wind_dir
        self.wind_strength = wind_strength
        self.width = width
        self.height = height

        # Set up model objects

        self.grid = OrthogonalMooreGrid((width, height), capacity=1, random=self.random)
        self.datacollector = mesa.DataCollector(
            {
                "Fine": lambda m: self.count_type(m, "Fine"),
                "On Fire": lambda m: self.count_type(m, "On Fire"),
                "Burned Out": lambda m: self.count_type(m, "Burned Out"),
            }
        )

        # Place a tree in each cell with Prob = density
        for cell in self.grid.all_cells:
            if self.random.random() < density:
                # Create a tree
                TreeCell(self, cell)

        self.ignite_initial_fire()
        self.running = True
        self.datacollector.collect(self)

    def ignite_initial_fire(self):
        # wind bias on: central ignitian

        if getattr(self, "wind_enabled", False):
            cx = self.width // 2
            cy = self.height // 2

            for x in range(cx - 4, cx + 5):
                for y in range(cy - 4, cy + 5):
                    for a in self.grid[(x, y)].agents:
                        a.condition = "On Fire"
            return
        # default: Set all trees in the first column on fire.
        for cell in self.grid.all_cells:
            if cell.coordinate[0] == 0:
                for a in cell.agents:
                    a.condition = "On Fire"

    def step(self):
        """Advance the model by one step."""
        self.agents.shuffle_do("step")
        # collect data
        self.datacollector.collect(self)

        # Halt if no more fire
        if self.count_type(self, "On Fire") == 0:
            self.running = False

    @staticmethod
    def count_type(model, tree_condition):
        """Helper method to count trees in a given condition in a given model."""
        return len(model.agents.select(lambda x: x.condition == tree_condition))

    # Wind Mechanisum

    def wind_unit_vector(self):
        """
        meteorological: 0° = from North, wind blows toward South
        return a unit vector (wx, wy) in grid coordinates
        """
        rad = math.radians(self.wind_dir)
        wx = -math.sin(rad)
        wy = -math.cos(rad)
        return (wx, wy)

    def wind_biased_multiplier(self, dx, dy):
        """Return multiplier >= 0 based on alignment with wind."""
        wx, wy = self.wind_unit_vector()
        norm = (dx * dx + dy * dy) ** 0.5
        if norm == 0:
            return 1.0
        dxu, dyu = dx / norm, dy / norm
        align = dxu * wx + dyu * wy  # [-1, 1]
        return max(0.0, 1.0 + (self.wind_strength * align))
