from mesa.discrete_space import CellAgent


class MineCell(CellAgent):
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell
        self.revealed = False
        self.neighbor_mines = 0

    def step(self):
        pass
