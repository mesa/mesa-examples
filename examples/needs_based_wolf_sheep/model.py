import mesa
from agents import NeedsBasedSheep, NeedsBasedWolf
from mesa.discrete_space import OrthogonalMooreGrid


class GrassPatch(mesa.Agent):
    def __init__(self, model, fully_grown):
        super().__init__(model)
        self.grass = fully_grown

    def step(self):
        if not self.grass and self.random.random() < self.model.grass_regrowth_rate:
            self.grass = True


class NeedsBasedWolfSheep(mesa.Model):
    """Wolf-Sheep with needs-based behavioral drives.

    Explores behavioral framework patterns from discussions #2538
    and #2526. Unlike standard Wolf-Sheep, agents prioritise
    actions based on drive urgency (hunger, fear) rather than
    checking all conditions every tick.

    Note: Population dynamics differ from standard Wolf-Sheep by
    design. Fear-suppressed eating in sheep can cause cascade
    extinction events — an emergent property of needs-based
    architecture that does not appear in the standard model.
    This difference is itself a finding worth exploring.
    """

    def __init__(
        self,
        width=40,
        height=40,
        initial_sheep=200,
        initial_wolves=15,
        sheep_reproduce=0.12,
        wolf_reproduce=0.04,
        grass_regrowth_rate=0.10,
        rng=None,
    ):
        super().__init__(rng=rng)
        self.sheep_reproduce = sheep_reproduce
        self.wolf_reproduce = wolf_reproduce
        self.grass_regrowth_rate = grass_regrowth_rate

        self.grid = OrthogonalMooreGrid(
            (width, height), torus=True, capacity=None, random=self.random
        )

        for cell in self.grid.all_cells:
            patch = GrassPatch(self, self.random.random() < 0.5)
            patch.cell = cell

        for _ in range(initial_sheep):
            cell = self.grid.all_cells.select_random_cell()
            sheep = NeedsBasedSheep(self, self.random.randint(4, 8))
            sheep.cell = cell

        for _ in range(initial_wolves):
            cell = self.grid.all_cells.select_random_cell()
            wolf = NeedsBasedWolf(self, self.random.randint(3, 6))
            wolf.cell = cell

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Wolves": lambda m: len(m.agents_by_type[NeedsBasedWolf]),
                "Sheep": lambda m: len(m.agents_by_type[NeedsBasedSheep]),
            }
        )

    def step(self):
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)


if __name__ == "__main__":
    model = NeedsBasedWolfSheep()
    for i in range(100):
        model.step()
        data = model.datacollector.get_model_vars_dataframe()
        print(
            f"Step {i + 1:3d}: "
            f"Wolves={int(data['Wolves'].iloc[-1]):3d}, "
            f"Sheep={int(data['Sheep'].iloc[-1]):3d}"
        )
    print("Done — model ran 100 steps successfully.")
