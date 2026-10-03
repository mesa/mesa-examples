from mesa.experimental.cell_space import FixedAgent


class NodeAgent(FixedAgent):
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell
