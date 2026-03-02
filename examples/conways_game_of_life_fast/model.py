import numpy as np
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.discrete_space import OrthogonalMooreGrid, PropertyLayer
from scipy.signal import convolve2d


class GameOfLifeModel(Model):
    def __init__(self, width=10, height=10, alive_fraction=0.2, rng=None):
        super().__init__(rng=rng)

        # Create grid and attach PropertyLayer to it
        self.grid = OrthogonalMooreGrid((width, height), torus=True, random=self.random)
        self.cell_layer = self.grid.create_property_layer("cell_layer", default_value=False, dtype=bool)

        # Randomly set cells to alive
        self.cell_layer.data = np.random.choice(
            [True, False],
            size=(width, height),
            p=[alive_fraction, 1 - alive_fraction]
        )

        # Metrics
        self.cells = width * height
        self.alive_count = 0
        self.alive_fraction = 0

        self.datacollector = DataCollector(
            model_reporters={
                "Cells alive": "alive_count",
                "Fraction alive": "alive_fraction",
            }
        )
        self.datacollector.collect(self)

    def step(self):
        kernel = np.array([[1, 1, 1],
                           [1, 0, 1],
                           [1, 1, 1]])

        neighbor_count = convolve2d(
            self.cell_layer.data, kernel, mode="same", boundary="wrap"
        )

        self.cell_layer.data = np.logical_or(
            np.logical_and(self.cell_layer.data,
                           np.logical_or(neighbor_count == 2, neighbor_count == 3)),
            np.logical_and(~self.cell_layer.data, neighbor_count == 3)
        )

        self.alive_count = np.sum(self.cell_layer.data)
        self.alive_fraction = self.alive_count / self.cells
        self.datacollector.collect(self)