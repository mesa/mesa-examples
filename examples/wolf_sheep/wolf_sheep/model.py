"""
Wolf-Sheep Predation Model
===========================
Replication of the NetLogo Wolf Sheep Predation model:
    Wilensky, U. (1997). http://ccl.northwestern.edu/netlogo/models/WolfSheepPredation.
    Center for Connected Learning and Computer-Based Modeling,
    Northwestern University, Evanston, IL.
"""

import math

import mesa
from mesa.datacollection import DataCollector
from mesa.discrete_space import OrthogonalMooreGrid

from .agents import GrassPatch, Sheep, Wolf


class WolfSheep(mesa.Model):
    """Wolf-Sheep Predation Model."""

    description = (
        "A model for simulating wolf and sheep (predator-prey) ecosystem dynamics."
    )

    def __init__(
        self,
        width=20,
        height=20,
        initial_sheep=100,
        initial_wolves=25,
        sheep_reproduce=0.04,
        wolf_reproduce=0.05,
        wolf_gain_from_food=20,
        grass=True,
        grass_regrowth_time=30,
        sheep_gain_from_food=4,
        rng=None,
    ):
        super().__init__(rng=rng)

        self.width = width
        self.height = height
        self.grass = grass

        self.grid = OrthogonalMooreGrid(
            [height, width],
            torus=True,
            capacity=math.inf,
            random=self.random,
        )

        model_reporters = {
            "Wolves": lambda m: len(m.agents_by_type[Wolf]),
            "Sheep": lambda m: len(m.agents_by_type[Sheep]),
        }
        if grass:
            model_reporters["Grass"] = lambda m: sum(
                1 for a in m.agents_by_type[GrassPatch] if a.fully_grown
            )

        self.datacollector = DataCollector(model_reporters)

        # Create sheep
        Sheep.create_agents(
            self,
            initial_sheep,
            energy=self.rng.random((initial_sheep,)) * 2 * sheep_gain_from_food,
            p_reproduce=sheep_reproduce,
            energy_from_food=sheep_gain_from_food,
            cell=self.random.choices(self.grid.all_cells.cells, k=initial_sheep),
        )

        # Create wolves
        Wolf.create_agents(
            self,
            initial_wolves,
            energy=self.rng.random((initial_wolves,)) * 2 * wolf_gain_from_food,
            p_reproduce=wolf_reproduce,
            energy_from_food=wolf_gain_from_food,
            cell=self.random.choices(self.grid.all_cells.cells, k=initial_wolves),
        )

        # Create grass patches
        if grass:
            for cell in self.grid:
                fully_grown = self.random.choice([True, False])
                countdown = (
                    0 if fully_grown else self.random.randrange(0, grass_regrowth_time)
                )
                GrassPatch(self, countdown, grass_regrowth_time, cell)

        self.running = True
        self.datacollector.collect(self)

    def step(self):
        self.agents_by_type[Sheep].shuffle_do("step")
        self.agents_by_type[Wolf].shuffle_do("step")
        self.datacollector.collect(self)
