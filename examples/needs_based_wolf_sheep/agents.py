from mesa.discrete_space import CellAgent


class NeedsBasedAnimal(CellAgent):
    """Base class with explicit internal drive states.
    Connects to Mesa discussion #2538 State Management component.
    """

    def __init__(self, model, energy):
        super().__init__(model)
        self.energy = energy
        self.hunger = 0.0
        self.fear = 0.0

    def update_drives(self):
        self.hunger = min(1.0, self.hunger + 0.03)
        self.fear = max(0.0, self.fear - 0.1)

    def move(self):
        self.cell = self.random.choice(list(self.cell.connections.values()))


class NeedsBasedWolf(NeedsBasedAnimal):
    def step(self):
        if self.cell is None:
            return
        self.move()
        self.energy -= 1
        self.update_drives()

        if self.energy <= 0:
            self.remove()
            return

        if self.hunger > 0.3:
            sheep = [a for a in self.cell.agents if isinstance(a, NeedsBasedSheep)]
            if sheep:
                prey = self.random.choice(sheep)
                self.energy += 6
                self.hunger = 0.0
                prey.remove()
                return

        if (
            self.energy > 20
            and self.fear < 0.3
            and self.hunger < 0.4
            and self.random.random() < self.model.wolf_reproduce
        ):
            self.energy //= 2
            NeedsBasedWolf(self.model, self.energy)


class NeedsBasedSheep(NeedsBasedAnimal):
    def step(self):
        if self.cell is None:
            return
        self.move()
        self.energy -= 1
        self.update_drives()

        wolves_nearby = sum(
            1 for a in self.cell.agents if isinstance(a, NeedsBasedWolf)
        )
        if wolves_nearby > 0:
            self.fear = min(1.0, self.fear + 0.5)

        if self.energy <= 0:
            self.remove()
            return

        if self.hunger > 0.5 and self.fear < 0.7 and self.cell.grass:
            self.energy += 4
            self.hunger = 0.0
            self.cell.grass = False
            return

        if (
            self.energy > 6
            and self.fear < 0.2
            and self.hunger < 0.3
            and self.random.random() < self.model.sheep_reproduce
        ):
            self.energy //= 2
            NeedsBasedSheep(self.model, self.energy)
