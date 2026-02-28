from mesa import Model
from mesa.space import MultiGrid

from .agent import CarAgent


class TraficFlow(Model):
    def __init__(self, width=20, height=5, n_cars=10, seed=None):
        super().__init__(seed=seed)

        self.grid = MultiGrid(width, height, torus=True)

        for _ in range(n_cars):
            car = CarAgent(self)

            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            while not self.grid.is_cell_empty((x, y)):
                x = self.random.randrange(self.grid.width)
                y = self.random.randrange(self.grid.height)
            self.grid.place_agent(car, (x, y))

    def step(self):
        self.agents.shuffle_do("step")
