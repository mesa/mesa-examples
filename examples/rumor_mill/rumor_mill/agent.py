from mesa.discrete_space import CellAgent


class Person(CellAgent):
    """A person who can know, spread, or forget a rumor."""

    def __init__(
        self,
        model,
        cell,
        rumor_spread_chance=0.5,
        skepticism=0.0,
        forget_chance=0.0,
        color=None,
    ):
        super().__init__(model)
        self.cell = cell
        self.knows_rumor = False
        self.times_heard = 0
        self.times_heard_this_step = 0
        self.newly_learned = False
        self.newly_forgotten = False
        self.rumor_spread_chance = rumor_spread_chance
        self.skepticism = skepticism
        self.forget_chance = forget_chance
        self.color = color if color is not None else "blue"

    def step(self):
        if self.knows_rumor:
            # forgetting mechanic
            if self.forget_chance > 0 and self.random.random() < self.forget_chance:
                self.knows_rumor = False
                self.newly_forgotten = True
                self.color = "blue"
                return

            neighbors = [
                agent for agent in self.cell.neighborhood.agents if agent != self
            ]
            if neighbors:
                neighbor = self.random.choice(neighbors)
                effective_spread = self.rumor_spread_chance * (1 - neighbor.skepticism)
                if not neighbor.knows_rumor and self.random.random() < effective_spread:
                    neighbor.knows_rumor = True
                    neighbor.newly_learned = True
                    neighbor.color = "red"
                neighbor.times_heard += 1
                neighbor.times_heard_this_step += 1


class Debunker(Person):
    """An agent that spreads a counter-rumor, actively telling neighbors the rumor is false."""

    def __init__(
        self,
        model,
        cell,
        rumor_spread_chance=0.5,
        skepticism=0.0,
        forget_chance=0.0,
        color=None,
    ):
        super().__init__(
            model, cell, rumor_spread_chance, skepticism, forget_chance, color
        )
        self.agent_type = "debunker"

    def step(self):
        neighbors = [agent for agent in self.cell.neighborhood.agents if agent != self]
        if neighbors:
            neighbor = self.random.choice(neighbors)
            if neighbor.knows_rumor and self.random.random() < self.rumor_spread_chance:
                neighbor.knows_rumor = False
                neighbor.newly_forgotten = True
                neighbor.color = "blue"
