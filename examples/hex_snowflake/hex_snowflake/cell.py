from mesa.discrete_space import FixedAgent


class Cell(FixedAgent):
    """Lightweight marker agent used only for visualization.

    The snowflake's frozen / empty state is stored in model.state_grid rather
    than inside this agent. This follows the pattern from Issue #366: patch
    agents that store only environment state are replaced by a grid-level
    NumPy array on the model.
    """

    def __init__(self, cell, model):
        """Place a visualization marker at the given grid cell."""
        super().__init__(model)
        self.cell = cell
