import mesa
from mesa.discrete_space import HexGrid

from .cell import Cell


class HexSnowflake(mesa.Model):
    """Represents the hex grid of cells. The grid is represented by a 2-dimensional array
    of cells with adjacency rules specific to hexagons.
    """

    def __init__(self, width=50, height=50, rng=None):
        """Create a new playing area of (width, height) cells."""
        super().__init__(rng=rng)
        # Use a hexagonal grid, where edges wrap around.
        self.grid = HexGrid((width, height), capacity=1, torus=True, random=self.random)

        # Place a dead cell at each location.
        for entry in self.grid.all_cells:
            Cell(entry, self)

        # activate the center(ish) cell.
        centerish_cell = self.grid[(width // 2, height // 2)]
        centerish_cell.agents[0].state = 1
        for a in centerish_cell.neighborhood.agents:
            a.is_considered = True

        self.running = True

    def step(self):
        """Perform the model step in two stages:
        - First, all cells assume their next state (whether they will be dead or alive)
        - Then, all cells change state to their next state
        """
        self.agents.do("determine_state")
        self.agents.do("assume_state")
