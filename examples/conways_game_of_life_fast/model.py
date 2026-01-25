import numpy as np
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import PropertyLayer
from scipy.signal import convolve2d


# fmt: off
class GameOfLifeModel(Model):
    def __init__(self, width=10, height=10, alive_fraction=0.2, randomize_new_cells=0.05):
        super().__init__()
        # Initialize the property layer for cell states
        self.cell_layer = PropertyLayer("cells", width, height, False, dtype=bool)
        # Randomly set cells to alive
        self.cell_layer.data = np.random.choice([True, False], size=(width, height), p=[alive_fraction, 1 - alive_fraction])

        # Metrics and datacollector
        self.cells = width * height
        self.alive_count = 0
        self.alive_fraction = 0
        self.randomize_new_cells = randomize_new_cells

        self.datacollector = DataCollector(
            model_reporters={"Cells alive": "alive_count",
                             "Fraction alive": "alive_fraction"}
        )
        self.datacollector.collect(self)

    def step(self):
        # Define a kernel for counting neighbors
        kernel = np.array([[1, 1, 1],
                           [1, 0, 1],
                           [1, 1, 1]])

        # Count neighbors using convolution
        neighbor_count = convolve2d(self.cell_layer.data, kernel, mode="same", boundary="wrap")

        """ Changing the behavior of cells so that they can "die from overpopulation"
        if there are more than 4 living neighbors around them. """

        # Apply Game of Life rules with overpopulation death:
        # 1. A live cell with 2 or 3 live neighbors survives.
        # 2. A live cell with more than 4 neighbors dies (overpopulation).
        # 3. A dead cell with exactly 3 live neighbors becomes alive.
        self.cell_layer.data = np.logical_or(
            np.logical_and(self.cell_layer.data, np.logical_and(neighbor_count >= 2, neighbor_count <= 3)),
            np.logical_and(~self.cell_layer.data, neighbor_count == 3)
        )

        # Оживлення нових клітин за ймовірністю randomize_new_cells
        if np.random.random() < self.randomize_new_cells:
            random_positions = np.random.choice([True, False], size=self.cell_layer.data.shape, p=[0.05, 0.95])
            self.cell_layer.data = np.logical_or(self.cell_layer.data, random_positions)

        # Metrics
        self.alive_count = np.sum(self.cell_layer.data)
        self.alive_fraction = self.alive_count / self.cells
        self.datacollector.collect(self)
