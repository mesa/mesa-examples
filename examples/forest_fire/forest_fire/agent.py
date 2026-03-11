from mesa.discrete_space import FixedAgent

class TreeCell(FixedAgent):
    """Tree cell used for visualization and grid coordinates."""

    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell
