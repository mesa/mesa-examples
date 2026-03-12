import mesa
from mesa.discrete_space import CellAgent, OrthogonalMooreGrid


class Walker(CellAgent):  # ← CellAgent not mesa.Agent
    def __init__(self, model, heading=(1, 0)):
        super().__init__(model)
        self.heading = heading
        self.headings = ((1, 0), (0, 1), (-1, 0), (0, -1))

    def step(self):
        new_cell = self.random.choice(list(self.cell.neighborhood))
        if new_cell.is_empty:
            self.cell = new_cell
        self.heading = self.random.choice(self.headings)


class ShapeExample(mesa.Model):
    def __init__(self, num_agents=5, width=20, height=10):
        super().__init__()
        self.num_agents = num_agents
        self.headings = ((1, 0), (0, 1), (-1, 0), (0, -1))
        self.grid = OrthogonalMooreGrid(
            (width, height), torus=True, random=self.random
        )
        self.make_walker_agents()
        self.running = True

    def make_walker_agents(self):
        cells = self.random.sample(list(self.grid.all_cells), self.num_agents)
        for cell in cells:
            heading = self.random.choice(self.headings)
            a = Walker(self, heading)
            a.cell = cell

    def step(self):
        self.agents.shuffle_do("step")