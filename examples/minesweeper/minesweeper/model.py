from mesa import Model
from mesa.discrete_space import OrthogonalMooreGrid, PropertyLayer

from .agents import MineCell


class MinesweeperModel(Model):
    """Discrete-space Minesweeper model."""

    def __init__(
        self,
        width=10,
        height=10,
        mine_density=0.15,
        seed=42,
    ):
        super().__init__(seed=seed)

        self.width = width
        self.height = height
        self.mine_density = mine_density
        self.game_over = False

        # Grid
        self.grid = OrthogonalMooreGrid(
            (width, height), torus=False, random=self.random
        )

        # Mine layer
        self.mine_layer = PropertyLayer(
            "mine", (width, height), default_value=False, dtype=bool
        )

        # Random mine placement
        self.mine_layer.data = self.rng.choice(
            [True, False],
            size=(width, height),
            p=[mine_density, 1 - mine_density],
        )

        self.grid.add_property_layer(self.mine_layer)

        # Create cell agents
        MineCell.create_agents(
            model=self,
            n=width * height,
            cell=self.grid.all_cells.cells,
        )

        self._count_neighbor_mines()

    # Game logic

    def _count_neighbor_mines(self):
        for cell in self.grid.all_cells:
            agent = cell.agents[0]

            if cell.mine:
                continue

            neighbors = cell.neighborhood
            agent.neighbor_mines = sum(n.mine for n in neighbors)

    def reveal_cell(self, cell):
        if self.game_over:
            return

        agent = cell.agents[0]

        if agent.revealed or agent.flagged:
            return

        agent.reveal()

        if cell.mine:
            self.game_over = True
            return

        if agent.neighbor_mines == 0:
            for n in cell.neighborhood:
                self.reveal_cell(n)

    def step(self):
        """Player-driven game → no automatic stepping."""
        pass
