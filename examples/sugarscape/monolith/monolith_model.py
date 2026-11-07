from pathlib import Path

import mesa
import numpy as np
from mesa.discrete_space import OrthogonalVonNeumannGrid
from mesa.discrete_space.property_layer import PropertyLayer

# Import from LOCAL agents file, not Mesa's built-in
from monolith_agents import Trader

# Helper Functions


def flatten(list_of_lists):
    return [item for sublist in list_of_lists for item in sublist]


def geometric_mean(list_of_prices):
    if len(list_of_prices) == 0:
        return -1
    return np.exp(np.log(list_of_prices).mean())


def drive_count(model, drive_name):
    """Count how many agents have a given active drive."""
    return sum(1 for a in model.agents if a.active_drive == drive_name)


class SugarscapeMonolith(mesa.Model):
    def __init__(
        self,
        width=50,
        height=50,
        initial_population=200,
        endowment_min=25,
        endowment_max=50,
        metabolism_min=1,
        metabolism_max=5,
        vision_min=1,
        vision_max=5,
        enable_trade=True,
        rng=None,
    ):
        super().__init__(rng=rng)
        self.width = width
        self.height = height
        self.enable_trade = enable_trade
        self.running = True

        # Initiate grid
        self.grid = OrthogonalVonNeumannGrid(
            (self.width, self.height), torus=False, random=self.random
        )

        # Read in landscape file
        self.sugar_distribution = np.genfromtxt(Path(__file__).parent / "sugar-map.txt")
        self.spice_distribution = np.flip(self.sugar_distribution, 1)

        sugar_layer = PropertyLayer("sugar", (self.width, self.height))
        sugar_layer.data[:] = self.sugar_distribution
        self.grid.add_property_layer(sugar_layer)

        spice_layer = PropertyLayer("spice", (self.width, self.height))
        spice_layer.data[:] = self.spice_distribution
        self.grid.add_property_layer(spice_layer)

        # DataCollector — original reporters plus drive distribution
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "#Traders": lambda m: len(m.agents),
                "Trade Volume": lambda m: sum(len(a.trade_partners) for a in m.agents),
                "Price": lambda m: geometric_mean(
                    flatten([a.prices for a in m.agents])
                ),
                # Drive distribution — this is the new data
                "Survive": lambda m: drive_count(m, "survive"),
                "Gather Sugar": lambda m: drive_count(m, "gather_sugar"),
                "Gather Spice": lambda m: drive_count(m, "gather_spice"),
                "Seek Trade": lambda m: drive_count(m, "seek_trade"),
                "Default": lambda m: drive_count(m, "default"),
            },
        )

        # Create trader agents
        n = initial_population
        Trader.create_agents(
            self,
            n,
            self.random.choices(self.grid.all_cells.cells, k=n),
            sugar=self.rng.integers(endowment_min, endowment_max, (n,), endpoint=True),
            spice=self.rng.integers(endowment_min, endowment_max, (n,), endpoint=True),
            metabolism_sugar=self.rng.integers(
                metabolism_min, metabolism_max, (n,), endpoint=True
            ),
            metabolism_spice=self.rng.integers(
                metabolism_min, metabolism_max, (n,), endpoint=True
            ),
            vision=self.rng.integers(vision_min, vision_max, (n,), endpoint=True),
        )

    def step(self):
        # Regrow sugar and spice (1 unit per tick, up to max)
        self.grid.sugar.data[:] = np.minimum(
            self.grid.sugar.data + 1, self.sugar_distribution
        )
        self.grid.spice.data[:] = np.minimum(
            self.grid.spice.data + 1, self.spice_distribution
        )

        # Step trader agents
        self.agents.shuffle_do("step")
        if self.enable_trade:
            self.agents.shuffle_do("trade_with_neighbors")
        self.datacollector.collect(self)

    def run_model(self, step_count=1000):
        for _ in range(step_count):
            self.step()
