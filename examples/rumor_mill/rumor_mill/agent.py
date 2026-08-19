from mesa.discrete_space import CellAgent


class Person(CellAgent):
    """
    A person agent that can know and spread a rumor.
    """

    def __init__(
        self, model, cell, rumor_spread_chance=0.5, color=None, recovery_rate=0.0
    ):
        """
        Initialize a Person agent.

        Args:
            model: The model instance
            cell: The cell where this agent is located
            rumor_spread_chance: Probability of successfully spreading rumor (0.0-1.0)
            color: Agent's color (red if knows rumor initially, blue otherwise)
        """
        super().__init__(model)
        self.cell = cell
        self.knows_rumor = False  # Whether agent knows the rumor
        self.times_heard = 0  # Total cumulative times agent has heard the rumor
        self.times_heard_this_step = 0  # Times heard in current step
        self.newly_learned = False  # Whether agent just learned the rumor this step
        self.has_known_rumor_before = False  # Whether agent has EVER known the rumor
        self.rumor_spread_chance = rumor_spread_chance
        self.recovery_rate = recovery_rate
        self.just_recovered = False
        self.color = color if color is not None else self.random.choice(["red", "blue"])

    def step(self):
        """
        Agent behavior each step: an informed agent may first forget the rumor (recover); otherwise, it tells a random neighbor.
        """
        if not self.knows_rumor:
            return

        # Chance to forget the rumor and become uninformed again
        if self.random.random() < self.recovery_rate:
            self.knows_rumor = False
            self.just_recovered = True
            return

        # Get all neighbors in the cell's neighborhood (excluding self)
        neighbors = [agent for agent in self.cell.neighborhood.agents if agent != self]
        if neighbors:
            # Randomly select one neighbor to tell
            neighbor = self.random.choice(neighbors)
            # Attempt to spread rumor with probability rumor_spread_chance
            if (
                not neighbor.knows_rumor
                and self.random.random() < self.rumor_spread_chance
            ):
                neighbor.knows_rumor = True
                if not neighbor.has_known_rumor_before:
                    neighbor.newly_learned = True  # Only true first-time learners
                neighbor.has_known_rumor_before = True
            # Increment times heard counters (even if already knew)
            # these two lines must stay inside the `if neighbors:` block
            neighbor.times_heard += 1
            neighbor.times_heard_this_step += 1
