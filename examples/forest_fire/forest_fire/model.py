import mesa
from mesa.discrete_space import OrthogonalMooreGrid

from .agent import TreeCell


class ForestFire(mesa.Model):
    """Simple Forest Fire model."""

    def __init__(self, width=100, height=100, density=0.65, rng=None):
        """Create a new forest fire model.

        Args:
            width, height: The size of the grid to model
            density: What fraction of grid cells have a tree in them.
        """
        super().__init__(rng=rng)

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
                new_tree = TreeCell(self, cell)
                # Set all trees in the first column on fire.
                if cell.coordinate[0] == 0:
                    new_tree.condition = "On Fire"

        self.running = True
        self.datacollector.collect(self)

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
