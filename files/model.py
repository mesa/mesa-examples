import mesa


class DemoAgent(mesa.Agent):
    """Moves to a random empty cell on every step."""

    def step(self):
        # Pick one of the 8 neighbouring cells (Moore neighbourhood).
        neighbours = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        new_pos = self.random.choice(neighbours)
        self.model.grid.move_agent(self, new_pos)


class Model(mesa.Model):
    """
    A 10×10 grid with 10 agents wandering around.
    Kept deliberately simple so CI can run it in under a second.
    """

    def __init__(self, n_agents: int = 10, width: int = 10, height: int = 10):
        super().__init__()
        self.grid = mesa.space.MultiGrid(width, height, torus=True)
        for _ in range(n_agents):
            agent = DemoAgent(self)
            x = self.random.randrange(width)
            y = self.random.randrange(height)
            self.grid.place_agent(agent, (x, y))

    def step(self):
        self.agents.shuffle_do("step")
