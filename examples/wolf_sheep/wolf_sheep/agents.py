from mesa.discrete_space import CellAgent, FixedAgent


class Animal(CellAgent):
    """Base class for Wolf and Sheep."""

    def __init__(self, model, energy, p_reproduce, energy_from_food, cell):
        super().__init__(model)
        self.energy = energy
        self.p_reproduce = p_reproduce
        self.energy_from_food = energy_from_food
        self.cell = cell

    def spawn_offspring(self):
        self.energy /= 2
        self.__class__(
            self.model,
            self.energy,
            self.p_reproduce,
            self.energy_from_food,
            self.cell,
        )

    def feed(self):
        pass

    def step(self):
        self.move()
        self.energy -= 1
        self.feed()
        if self.energy < 0:
            self.remove()
        elif self.random.random() < self.p_reproduce:
            self.spawn_offspring()


class Sheep(Animal):
    """A sheep that eats grass and can be eaten by wolves."""

    def feed(self):
        grass = next(
            (a for a in self.cell.agents if isinstance(a, GrassPatch)), None
        )
        if grass and grass.fully_grown:
            self.energy += self.energy_from_food
            grass.get_eaten()

    def move(self):
        safe_cells = [
            c for c in self.cell.neighborhood
            if not any(isinstance(a, Wolf) for a in c.agents)
        ]
        target = safe_cells or list(self.cell.neighborhood)
        if target:
            self.cell = self.random.choice(target)


class Wolf(Animal):
    """A wolf that eats sheep."""

    def feed(self):
        sheep = [a for a in self.cell.agents if isinstance(a, Sheep)]
        if sheep:
            prey = self.random.choice(sheep)
            self.energy += self.energy_from_food
            prey.remove()

    def move(self):
        cells_with_sheep = [
            c for c in self.cell.neighborhood
            if any(isinstance(a, Sheep) for a in c.agents)
        ]
        target = cells_with_sheep or list(self.cell.neighborhood)
        if target:
            self.cell = self.random.choice(target)


class GrassPatch(FixedAgent):
    """A patch of grass that regrows after being eaten."""

    def __init__(self, model, countdown, grass_regrowth_time, cell):
        super().__init__(model)
        self.grass_regrowth_time = grass_regrowth_time
        self.cell = cell
        self.fully_grown = countdown == 0
        if not self.fully_grown:
            self.model.schedule_event(self.regrow, after=countdown)

    def regrow(self):
        self.fully_grown = True

    def get_eaten(self):
        self.fully_grown = False
        self.model.schedule_event(self.regrow, after=self.grass_regrowth_time)
