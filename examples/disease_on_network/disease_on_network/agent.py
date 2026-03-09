import mesa
from mesa.discrete_space import CellAgent
from enum import IntEnum
from typing import Dict


class State(IntEnum):
    SUSCEPTIBLE = 0
    INFECTED = 1
    RECOVERED = 2
    DEAD = 3


class PersonAgent(CellAgent):
    """
    An agent representing a person on the graph.


    Attributes:
        state: Current state of the agent (SUSCEPTIBLE, INFECTED, RECOVERED, DEAD).
        mod_infect: Modifier for infection probability.
        mod_recover: Modifier for recovery probability.
        mod_caution: Modifier for caution threshold.
        wants_open: Whether the agent wants to keep links open.
    """

    def __init__(
        self,
        model: mesa.Model,
        mod_infect: float,
        mod_recover: float,
        mod_caution: float,
    ) -> None:
        """Initialize a new agent."""

        super().__init__(model)
        self.state = State.SUSCEPTIBLE
        self.mod_infect = mod_infect
        self.mod_recover = mod_recover
        self.mod_caution = mod_caution
        self.link_opinions: Dict[int, bool] = {}

    def update_link_opinions(self, link_activity: float) -> None:
        """
        Decide for each neighbor individually whether to keep the link open.
        """
        if self.state == State.DEAD:
            # If dead, every link already set to false
            return

        # Iterate over neighbor cells
        for neighbor_cell in self.cell.neighborhood:
            nid = neighbor_cell.coordinate

            # Initialize if not present
            if nid not in self.link_opinions:
                self.link_opinions[nid] = True

            # High global caution = lower threshold to close links
            threshold = link_activity * (1.0 / self.mod_caution)

            self.link_opinions[nid] = self.model.random.random() < threshold

    def step(self) -> None:
        if self.state == State.DEAD:
            return

        # Disease dynamics
        if self.state == State.INFECTED:
            self._try_infect_neighbors()
            self._try_recover_or_die()

    def _try_infect_neighbors(self) -> None:
        """
        Attempts to infect neighbors via active links only.
        """

        # Loop on the neighbors
        for neighbor_cell in self.cell.neighborhood:
            if not neighbor_cell.agents:
                continue

            neighbor_agent = neighbor_cell.agents[0]
            nid = neighbor_cell.coordinate

            # Update link status
            my_opinion = self.link_opinions.get(nid, True)
            their_opinion = neighbor_agent.link_opinions.get(self.cell.coordinate, True)

            # Only active links spread infection
            if not (my_opinion and their_opinion):
                continue

            # Try infection
            if neighbor_agent.state == State.SUSCEPTIBLE:
                prob = self.model.pt * self.mod_infect

                if self.model.random.random() < prob:
                    neighbor_agent.state = State.INFECTED

    def _try_recover_or_die(self) -> None:
        """
        Determines if the agent recovers or dies.
        """

        # Try die
        if self.model.random.random() < self.model.pm:
            self.state = State.DEAD

            # Set all existing link opinions to False
            self.link_opinions = {nid: False for nid in self.link_opinions}
            return

        # Try recover
        if self.model.random.random() < (self.model.pr * self.mod_recover):
            self.state = State.RECOVERED
