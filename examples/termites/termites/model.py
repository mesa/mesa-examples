from mesa import Model
from mesa.discrete_space import OrthogonalMooreGrid, PropertyLayer

from .agents import Termite


class TermiteModel(Model):
    """A simulation that shows behavior of termite agents gathering wood chips into piles."""

    def __init__(
        self, num_termites=100, width=100, height=100, wood_chip_density=0.1, rng=42
    ):
        """Initialize the model.

        Args:
            num_termites: Number of Termite Agents,
            width: Grid width.
            height: Grid heights.
            wood_chip_density: Density of wood chips in the grid.
            rng : Random number generator for reproducibility.
        """
        super().__init__(rng=42)
        self.num_termites = num_termites
        self.wood_chip_density = wood_chip_density

        self.grid = OrthogonalMooreGrid((width, height), torus=True, random=self.random)

        self.wood_chips_layer = PropertyLayer(
            "woodcell", (width, height), default_value=False, dtype=bool
        )

        # Randomly distribute wood chips, by directly modifying the layer's underlying ndarray
        self.wood_chips_layer.data = self.rng.choice(
            [True, False],
            size=(width, height),
            p=[self.wood_chip_density, 1 - self.wood_chip_density],
        )

        self.grid.add_property_layer(self.wood_chips_layer)

        # Create agents and randomly distribute them over the grid
        Termite.create_agents(
            model=self,
            n=self.num_termites,
            cell=self.random.sample(self.grid.all_cells.cells, k=self.num_termites),
        )

    def step(self):
        self.agents.shuffle_do("step")
