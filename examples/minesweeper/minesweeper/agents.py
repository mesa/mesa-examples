from mesa.discrete_space import CellAgent


class MineCell(CellAgent):
    """A single Minesweeper cell."""

    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell

        self.revealed = False
        self.flagged = False
        self.neighbor_mines = 0

    def reveal(self):
        if self.revealed or self.flagged:
            return
        self.revealed = True
