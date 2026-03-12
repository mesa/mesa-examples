import numpy as np
import mesa
from mesa.discrete_space import HexGrid

from .cell import Cell

# Environment state is stored on the model as a NumPy array instead of inside
# individual Cell agents. Each grid position is represented by a value in
# state_grid (0 = empty, 1 = frozen) and a boolean in is_considered that
# tracks which cells sit on the frontier of the growing snowflake. Only
# frontier cells check their neighbors each step, preserving the original
# performance optimization.


class HexSnowflake(mesa.Model):
    """Represents the hex grid of cells. The grid is represented by a 2-dimensional
    array of cells with adjacency rules specific to hexagons.

    Environment state (frozen / empty) lives in model.state_grid rather than
    inside agent objects, following the pattern from Issue #366.
    """

    def __init__(self, width=50, height=50, rng=None):
        """Create a new playing area of (width, height) cells."""
        super().__init__(rng=rng)

        # Use a hexagonal grid where edges wrap around.
        self.grid = HexGrid((width, height), capacity=1, torus=True, random=self.random)

        # Create a lightweight Cell agent at each position for visualization.
        for entry in self.grid.all_cells:
            Cell(entry, self)

        # Environment state stored as a NumPy array: 0 = empty, 1 = frozen.
        self.state_grid = np.zeros((width, height), dtype=np.int8)

        # Track which cells are on the frontier (adjacent to at least one
        # frozen cell). Only frontier cells are evaluated each step.
        self.is_considered = np.zeros((width, height), dtype=bool)

        # Seed the snowflake at the center cell.
        cx, cy = width // 2, height // 2
        self.state_grid[cx, cy] = 1

        # Mark the neighbors of the seed as frontier cells.
        centerish_cell = self.grid[(cx, cy)]
        for neighbor in centerish_cell.neighborhood:
            nx, ny = neighbor.coordinate
            self.is_considered[nx, ny] = True

        self.running = True

    def step(self):
        """Advance the snowflake by one tick.

        A dead cell on the frontier becomes frozen if exactly one of its
        neighbors is already frozen. The frontier expands to include the
        neighbors of any newly frozen cell.

        State is computed into new_state before being applied so that all
        cells use the same snapshot of the grid, matching the original
        two-phase determine_state / assume_state design. We iterate over
        Cell agents (via self.agents) rather than the grid's CellCollection
        because AgentSet iteration is significantly faster.
        """
        new_state = self.state_grid.copy()
        new_considered = self.is_considered.copy()

        for agent in self.agents:
            x, y = agent.cell.coordinate

            if self.state_grid[x, y] == 1:
                continue  # already frozen, nothing to do

            if not self.is_considered[x, y]:
                continue  # not on the frontier, skip for performance

            live_neighbors = sum(
                self.state_grid[nx, ny]
                for n in agent.cell.neighborhood
                for nx, ny in [n.coordinate]
            )

            if live_neighbors == 1:
                new_state[x, y] = 1
                # Expand the frontier to include this cell's neighbors.
                for n in agent.cell.neighborhood:
                    nx, ny = n.coordinate
                    new_considered[nx, ny] = True

        self.state_grid = new_state
        self.is_considered = new_considered
