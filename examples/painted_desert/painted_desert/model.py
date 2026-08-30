import mesa
from mesa.discrete_space import OrthogonalMooreGrid

from .agents import ChipCollector


class ChipCollectorModel(mesa.Model):
    """Model simulating chip collectors organizing wood chips on patches."""

    def __init__(
        self, width=50, height=50, density=40, number=150, colors=4, seed=None
    ):
        """Initialize the model.

        Args:
            width: Width of the grid.
            height: Height of the grid.
            density: Probability (0-100) that a patch will have a colored chip initially.
            number: Number of chip collector agents.
            colors: Number of different chip colors.
            seed: Random seed for reproducibility.
        """
        super().__init__(seed=seed)
        self.width = width
        self.height = height
        self.density = density
        self.number = number
        self.colors = colors

        # Create grid
        self.grid = OrthogonalMooreGrid((width, height), random=self.random)

        # Create property layer for patch colors (pcolor)
        # 0 = black (empty), other values = colored chips
        self.grid.create_property_layer("pcolor", default_value=0, dtype=int)

        # Initialize patches with colored chips based on density
        self._setup_patches()

        # Create chip collector agents
        self._setup_agents()

    def _setup_patches(self):
        """Initialize patches with colored chips based on density parameter."""
        for cell in self.grid.all_cells:
            # If random number < density, set a colored chip
            if self.random.random() * 100 < self.density:
                chip_color = self.random.randint(1, self.colors)
                cell.pcolor = chip_color

    def _setup_agents(self):
        """Create chip collector agents at random positions."""
        # Generate random positions for agents
        all_cells = list(self.grid.all_cells.cells)
        selected_cells = self.random.choices(all_cells, k=self.number)

        # Create agents (they will pick up any chip they find)
        for cell in selected_cells:
            ChipCollector(self, cell, self.random.randint(1, self.colors))
            # Agent is already initialized with cell, so we don't need to move it

    def step(self):
        """Execute one time step of the model."""
        # Shuffle and execute all agents' step methods
        self.agents.shuffle_do("step")
