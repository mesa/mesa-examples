from mesa import Model
from mesa.discrete_space import OrthogonalMooreGrid
 
from .agent import CarAgent


class TraficFlow(Model):
    def __init__(self, width=20, height=5, n_cars=10, seed=None):
        super().__init__(seed=seed)
        
        self.grid = OrthogonalMooreGrid([width, height], torus=True, random=self.random)

        for _ in range(n_cars):
            car = CarAgent(self)

            x = self.random.randrange(self.grid.dimensions[0])
            y = self.random.randrange(self.grid.dimensions[1])
            while len(self.grid._cells[(x, y)].agents) > 0:
                x = self.random.randrange(self.grid.dimensions[0])
                y = self.random.randrange(self.grid.dimensions[1])
            self.grid._cells[(x, y)].add_agent(car)
            car.pos = (x, y)

    def step(self):
        self.agents.shuffle_do("step")
