from enum import Enum, auto

from mesa.discrete_space import CellAgent


class AntState(Enum):
    FORAGING = auto()
    RETURNING = auto()


class Ant(CellAgent):
    """
    An Ant agent that navigates the HexGrid using pheromones.
    """

    def __init__(self, model):
        super().__init__(model)
        self.state = AntState.FORAGING
        self.carrying_food = False

        # Randomly wiggle to avoid stacked agents looking static
        self.wiggle_bias = self.random.uniform(-0.1, 0.1)

    def step(self):
        """
        Agent Life Cycle:
        1. SENSE: Check neighbors.
        2. DECIDE: Switch state if needed.
        3. ACT: Move and deposit pheromones.
        """

        # --- State Logic ---
        if self.state == AntState.FORAGING:
            self._step_foraging()
        elif self.state == AntState.RETURNING:
            self._step_returning()

    def _step_foraging(self):
        # 1. Check if we found food
        if self.cell.food > 0:
            self._pickup_food()
            return

        # 2. Drop "Home" pheromone
        current_val = self.cell.pheromone_home
        self.cell.pheromone_home = min(current_val + 1.0, 10.0)

        # 3. Move
        # Look for Food Pheromone
        self._move_towards_gradient("pheromone_food", randomness=0.3)

    def _step_returning(self):
        # 1. Check if we are home
        if self.cell.home:
            self._drop_food()
            return

        # 2. Drop "Food" pheromone
        current_val = self.cell.pheromone_food
        self.cell.pheromone_food = min(current_val + 2.0, 10.0)

        # 3. Move
        # Look for Home Pheromone
        self._move_towards_gradient("pheromone_home", randomness=0.1)

    def _pickup_food(self):
        """Interact with environment to take food."""
        self.cell.food -= 1
        self.carrying_food = True
        self.state = AntState.RETURNING

    def _drop_food(self):
        """Interact with environment to drop food."""
        # Infinite storage at home
        self.carrying_food = False
        self.state = AntState.FORAGING

    def _move_towards_gradient(self, layer_name, randomness=0.1):
        """
        Find the neighbor with the highest value in 'layer_name'.
        With some probability, move randomly to explore.
        """
        if self.random.random() < randomness:
            # Explore: Random Move
            target = self.cell.neighborhood.select_random_cell()
            self.move_to(target)
            return

        # Exploit: Gradient Ascent
        best_cell = self.cell
        best_val = -1.0

        # Check all neighbors
        for neighbor in self.cell.neighborhood:
            # Access the property dynamically
            val = getattr(neighbor, layer_name)
            if val > best_val:
                best_val = val
                best_cell = neighbor

        # If we found a better cell (or at least valid one), move
        if best_cell != self.cell:
            self.move_to(best_cell)
        else:
            # Local maxima or flat ground: Random walk
            target = self.cell.neighborhood.select_random_cell()
            self.move_to(target)
