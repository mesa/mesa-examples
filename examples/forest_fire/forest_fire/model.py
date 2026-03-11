import mesa
import numpy as np
from mesa.discrete_space import OrthogonalMooreGrid

from .agent import TreeCell

# Environment state stored as NumPy array instead of patch agents.
# This simplifies the model and avoids creating thousands of objects
# when cells only store state.

FINE = 0
ON_FIRE = 1
BURNED_OUT = 2
EMPTY = -1

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
        
        # Environment state stored in NumPy array instead of patch agents.
        # TreeCell agents are kept only as lightweight wrappers for visualization.
        # State array
        self.fire_state = np.full((width, height), EMPTY, dtype=np.int8)

        self.datacollector = mesa.DataCollector(
            {
                "Fine": lambda m: int(np.sum(m.fire_state == FINE)),
                "On Fire": lambda m: int(np.sum(m.fire_state == ON_FIRE)),
                "Burned Out": lambda m: int(np.sum(m.fire_state == BURNED_OUT)),
            }
        )

        # Place a tree in each cell with Prob = density
        for cell in self.grid.all_cells:
            # Create a tree wrapper
            tree = TreeCell(self, cell)
            # self.grid.place_agent(tree, cell)  # Not needed/supported in OrthogonalMooreGrid
            
            x, y = cell.coordinate
            if self.random.random() < density:
                self.fire_state[x, y] = FINE
                # Set all trees in the first column on fire.
                if x == 0:
                    self.fire_state[x, y] = ON_FIRE

        self.running = True
        self.datacollector.collect(self)

    def step(self):
        """Advance the model by one step."""
        
        new_fire_state = self.fire_state.copy()
        
        for cell in self.grid.all_cells:
            x, y = cell.coordinate
            if self.fire_state[x, y] == ON_FIRE:
                for neighbor in cell.neighborhood:
                    nx, ny = neighbor.coordinate
                    if self.fire_state[nx, ny] == FINE:
                        new_fire_state[nx, ny] = ON_FIRE
                new_fire_state[x, y] = BURNED_OUT

        self.fire_state = new_fire_state
        
        # collect data
        self.datacollector.collect(self)

        # Halt if no more fire
        if np.sum(self.fire_state == ON_FIRE) == 0:
            self.running = False
