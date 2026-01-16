from mesa import Model
from mesa.discrete_space import OrthogonalMooreGrid, PropertyLayer

from .agents import MineCell


class MinesweeperModel(Model):
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
        self.win = False

        # Grid
        self.grid = OrthogonalMooreGrid(
            (width, height),
            torus=False,
            random=self.random,
        )

        # Mine layer
        self.mine_layer = PropertyLayer(
            "mine",
            (width, height),
            default_value=False,
            dtype=bool,
        )

        self.mine_layer.data = self.rng.choice(
            [True, False],
            size=(width, height),
            p=[mine_density, 1 - mine_density],
        )

        self.grid.add_property_layer(self.mine_layer)

        # One agent per cell
        MineCell.create_agents(
            model=self,
            n=width * height,
            cell=self.grid.all_cells.cells,
        )

        self._count_neighbor_mines()

    def _count_neighbor_mines(self):
        for cell in self.grid.all_cells:
            agent = cell.agents[0]
            if cell.mine:
                continue
            agent.neighbor_mines = sum(n.mine for n in cell.neighborhood)

    def reveal_cell(self, cell):
        if self.game_over:
            return

        agent = cell.agents[0]

        if agent.revealed or agent.flagged:
            return

        agent.reveal()

        # Mine clicked
        if cell.mine:
            self.game_over = True
            self._reveal_all_mines()
            return

        # Flood fill
        if agent.neighbor_mines == 0:
            for neighbor in cell.neighborhood:
                self.reveal_cell(neighbor)

        self._check_win()

    def _reveal_all_mines(self):
        for cell in self.grid.all_cells:
            if cell.mine:
                cell.agents[0].revealed = True

    def _check_win(self):
        for cell in self.grid.all_cells:
            agent = cell.agents[0]
            if not cell.mine and not agent.revealed:
                return
        self.win = True
        self.game_over = True

    def step(self):
        # Player-driven game
        pass
