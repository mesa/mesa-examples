from mesa.discrete_space import FixedAgent


class Cell(FixedAgent):
    """Represents a single ALIVE or DEAD cell in the simulation."""

    DEAD = 0
    ALIVE = 1

    def __init__(self, cell, model, init_state=DEAD):
        """Create a cell, in the given state, at the given x, y position."""
        super().__init__(model)
        self.cell = cell
        self.state = init_state
        self._next_state = None
        self.is_considered = False

    @property
    def is_alive(self):
        return self.state == self.ALIVE

    @property
    def considered(self):
        return self.is_considered is True

    def determine_state(self):
        """Compute if the cell will be dead or alive at the next tick. A dead
        cell will become alive if it has only one neighbor. The state is not
        changed here, but is just computed and stored in self._next_state,
        because our current state may still be necessary for our neighbors
        to calculate their next state.
        When a cell is made alive, its neighbors are able to be considered
        in the next step. Only cells that are considered check their neighbors
        for performance reasons.
        """
        # assume no state change
        self._next_state = self.state

        if not self.is_alive and self.is_considered:
            # Get the neighbors and apply the rules on whether to be alive or dead
            # at the next tick.
            live_neighbors = sum(
                neighbor.is_alive for neighbor in self.cell.neighborhood.agents
            )

            if live_neighbors == 1:
                self._next_state = self.ALIVE
                for a in self.cell.neighborhood.agents:
                    a.is_considered = True

    def assume_state(self):
        """Set the state to the new computed state"""
        self.state = self._next_state
