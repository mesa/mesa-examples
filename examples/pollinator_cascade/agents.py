from mesa.discrete_space import CellAgent


class Pollinator(CellAgent):
    """
    Pollinator agent (bee, butterfly, etc.) that forages from
    connected plant nodes. Dies if energy runs out.

    Attributes:
        specialization: 0 = generalist, 1 = specialist.
        energy: Current energy level (0 to 1).
        alive: Whether this agent is still active.
    """

    def __init__(self, model, cell, specialization: float):
        super().__init__(model)
        self.cell = cell
        self.specialization = specialization
        self.energy = 1.0
        self.alive = True

    def forage(self):
        if not self.alive:
            return

        # Get all plant agents on neighboring cells
        neighboring_cells = list(self.cell.connections.values())
        connected_plants = [
            a for c in neighboring_cells for a in c.agents if isinstance(a, Plant)
        ]
        alive_plants = [p for p in connected_plants if p.alive]

        if not connected_plants:
            self.energy -= 0.15
        elif not alive_plants:
            self.energy -= 0.12
        else:
            # Gain energy based on fraction of plants still alive
            support_ratio = len(alive_plants) / len(connected_plants)
            self.energy += support_ratio * 0.04

        # Specialists pay more energy per step than generalists
        baseline_cost = 0.04 + self.specialization * 0.04
        self.energy -= baseline_cost
        self.energy = max(0.0, min(1.0, self.energy))

        if self.energy <= 0:
            self.alive = False

    def step(self):
        self.forage()


class Plant(CellAgent):
    """
    Plant agent that depends on pollinators to stay healthy.
    Health drops when pollinator partners die.

    Attributes:
        resilience: 0 = fragile, 1 = highly resilient.
        health: Current health level (0 to 1).
        alive: Whether this agent is still active.
    """

    def __init__(self, model, cell, resilience: float):
        super().__init__(model)
        self.cell = cell
        self.resilience = resilience
        self.health = 1.0
        self.alive = True

    def update_health(self):
        if not self.alive:
            return

        # Get all pollinator agents on neighboring cells
        neighboring_cells = list(self.cell.connections.values())
        connected_pollinators = [
            a for c in neighboring_cells for a in c.agents if isinstance(a, Pollinator)
        ]

        if not connected_pollinators:
            self.health -= 0.04
        else:
            alive_pollinators = [p for p in connected_pollinators if p.alive]
            support_ratio = len(alive_pollinators) / len(connected_pollinators)

            if support_ratio >= 0.8:
                # Enough pollinators alive - slowly recover
                self.health += 0.01 * (1 - self.resilience * 0.3)
            else:
                # Too many pollinators lost - health declines
                decline = (0.8 - support_ratio) * 0.04
                decline *= 1 - self.resilience * 0.5
                self.health -= decline

        self.health = max(0.0, min(1.0, self.health))

        # Fragile plants die at higher health values than resilient ones
        death_threshold = 0.05 + (1 - self.resilience) * 0.30
        if self.health <= death_threshold:
            self.alive = False
            self.health = 0

    def step(self):
        self.update_health()
