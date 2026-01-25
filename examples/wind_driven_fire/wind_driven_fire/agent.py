import mesa


class Tree(mesa.Agent):
    """A tree cell.

    Attributes:
        condition : "Fine", "On Fire", "Burned Out"
    """

    def __init__(self, model, condition="Fine"):
        super().__init__(model)
        self.condition = condition

    def step(self):
        if self.condition != "On Fire":
            return

        # Spread fire (8-neighborhood)
        neighbors = self.model.grid.get_neighbors(
            self.pos, moore=True, include_center=False
        )

        for n in neighbors:
            if n.condition != "Fine":
                continue
            # Calculate wind bias
            dx = n.pos[0] - self.pos[0]
            dy = n.pos[1] - self.pos[1]
            # wind direction influence factor
            factor = self.model.wind_biased_probability(dx, dy)
            p = self.model.p_spread * factor

            if self.model.random.random() < p:
                n.condition = "On Fire"

        # After spreading fire, this tree burns out
        self.condition = "Burned Out"
