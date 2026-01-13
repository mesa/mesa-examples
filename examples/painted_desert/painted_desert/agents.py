from mesa.discrete_space import Grid2DMovingAgent


class ChipCollector(Grid2DMovingAgent):
    """Represents a termite that collects and organizes colored wood chips."""

    def __init__(self, model, cell, color):
        """
        Initialize the chip collector agent.

        Args:
            model: The associated ChipCollectorModel instance.
            cell: Initial cell.
            color: Initial chip color.
        """
        super().__init__(model)
        self.cell = cell
        self.chip_color = color
        self.chip = False
        self.visual_color = -1  # White when not carrying

    def wiggle(self):
        """Move forward 1 step, then turn random angle (-50 to +50 degrees).
        In discrete grid: move to a random neighbor (simulating forward + random turn)."""
        neighbors = list(self.cell.neighborhood)
        if neighbors:
            self.cell = self.random.choice(neighbors)

    def get_away(self):
        """Turn random direction, move back 10 steps, stop if on empty (black) cell.
        Executes recursively (iteratively) until on empty cell."""
        # Keep moving back until on empty cell
        while True:
            # Turn random direction, move back 10 steps
            for _ in range(10):
                neighbors = list(self.cell.neighborhood)
                if neighbors:
                    self.cell = self.random.choice(neighbors)
            # Stop if on empty (black) cell
            if self.cell.pcolor == 0:  # black = empty
                return  # stop

    def find_chip(self):
        """Find a wood chip and pick it up.
        Executes recursively (iteratively) until chip is found and picked up."""
        # Keep searching until chip is found
        while True:
            if self.cell.pcolor == self.chip_color:  # if wood-chip is my color
                # Pick up the chip
                self.cell.pcolor = 0  # Set patch to empty (black)
                self.chip = True
                self.visual_color = self.chip_color
                # Get away from this spot
                self.get_away()
                return  # stop
            # Wiggle and continue searching
            self.wiggle()

    def find_new_pile(self):
        """Find another wood chip of the same color.
        Executes recursively (iteratively) until matching chip is found."""
        # Keep searching until matching chip is found
        while True:
            if self.cell.pcolor == self.chip_color:  # Found matching chip
                return  # stop
            # Move forward 10 steps (move 10 times to random neighbors)
            for _ in range(10):
                neighbors = list(self.cell.neighborhood)
                if neighbors:
                    self.cell = self.random.choice(neighbors)
            # Wiggle
            self.wiggle()

    def find_empty_spot(self):
        """Find a place to put down wood chip.
        Executes recursively (iteratively) until empty spot is found and chip is put down."""
        # Keep searching until empty spot is found
        while True:
            if (
                self.cell.pcolor == 0
            ):  # if find a patch without a wood chip (black = empty)
                # Put down the chip
                self.cell.pcolor = self.chip_color
                self.chip = False
                self.visual_color = -1  # white
                # Move forward 20 steps
                for _ in range(20):
                    neighbors = list(self.cell.neighborhood)
                    if neighbors:
                        self.cell = self.random.choice(neighbors)
                return  # stop
            # Turn random direction (wiggle) and move forward 1
            self.wiggle()

    def step(self):
        """Execute agent behavior in one time step.

        Main procedure (go):
        - If not carrying: find-chip
        - If carrying: find-new-pile, then find-empty-spot
        """
        if not self.chip:
            # Not carrying a chip: find-chip
            self.find_chip()
        else:
            # Carrying a chip: find-new-pile, then find-empty-spot
            self.find_new_pile()
            self.find_empty_spot()
