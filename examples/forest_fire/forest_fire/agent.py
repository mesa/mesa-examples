from mesa.discrete_space import FixedAgent


class TreeCell(FixedAgent):
    """A tree cell.

    Attributes:
        condition: Can be "Fine", "On Fire", or "Burned Out"

    """

    def __init__(self, model, cell):
        """Create a new tree.

        Args:
            model: standard model reference for agent.
        """
        super().__init__(model)
        self.condition = "Fine"
        self.cell = cell

    def step(self):
        """If the tree is on fire, spread it to fine trees nearby."""
        if self.condition == "On Fire":
            for neighbor in self.cell.neighborhood.agents:
                if neighbor.condition != "Fine":
                    continue

                # Backward-compatible default: deterministic spread
                if self.model.p_spread is None:
                    neighbor.condition = "On Fire"
                    continue

                # Optional probabilistic spread: apply wind bias only if enabled
                dx = neighbor.cell.coordinate[0] - self.cell.coordinate[0]
                dy = neighbor.cell.coordinate[1] - self.cell.coordinate[1]

                factor = 1.0
                if (
                    getattr(self.model, "wind_enabled", False)
                    and getattr(self.model, "wind_strength", 0.0) > 0
                ):
                    factor = self.model.wind_biased_multiplier(dx, dy)

                p = self.model.p_spread * factor
                p = 0.0 if p < 0 else (1.0 if p > 1.0 else p)

                if self.model.random.random() < p:
                    neighbor.condition = "On Fire"

            self.condition = "Burned Out"
