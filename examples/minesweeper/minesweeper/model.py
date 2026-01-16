from mesa import Model
from mesa.datacollection import DataCollector
from mesa.discrete_space import OrthogonalMooreGrid, PropertyLayer

from .agents import MineCell


class MinesweeperModel(Model):
    def __init__(self, width=10, height=10, mine_density=0.15, seed=42):
        super().__init__(seed=seed)

        self.game_over = False
        self.frontier = set()

        self.grid = OrthogonalMooreGrid(
            (width, height),
            torus=False,
            random=self.random,
        )

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

        MineCell.create_agents(
            model=self,
            n=width * height,
            cell=self.grid.all_cells.cells,
        )

        for cell in self.grid.all_cells:
            cell.agents[0].neighbor_mines = sum(n.mine for n in cell.neighborhood)

        safe = [c for c in self.grid.all_cells if not c.mine]
        self.frontier |= set(self.random.sample(safe, k=5))

        self.datacollector = DataCollector(
            model_reporters={
                "Revealed": lambda m: sum(a.revealed for a in m.agents),
                "Frontier": lambda m: len(m.frontier),
            }
        )

        self.datacollector.collect(self)

    def step(self):
        if self.game_over:
            return

        if not self.frontier:
            hidden_safe = [
                c
                for c in self.grid.all_cells
                if not c.mine and not c.agents[0].revealed
            ]
            if not hidden_safe:
                return
            self.frontier.add(self.random.choice(hidden_safe))

        next_frontier = set()

        for cell in self.frontier:
            agent = cell.agents[0]

            if agent.revealed:
                continue

            agent.revealed = True

            if cell.mine:
                self.game_over = True
                return

            if agent.neighbor_mines == 0:
                for n in cell.neighborhood:
                    if not n.agents[0].revealed:
                        next_frontier.add(n)

        self.frontier = next_frontier
        self.datacollector.collect(self)
