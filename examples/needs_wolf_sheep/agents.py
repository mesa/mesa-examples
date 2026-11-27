"""
Needs-Based Wolf-Sheep Agents
==============================

Extends Mesa's core Wolf-Sheep model with continuous internal states
(hunger, fear, fatigue) that drive behavior through priority-based
decision-making. Built as a behavioral framework evaluation for GSoC 2026.

Key differences from core Wolf-Sheep:
- Agents have continuous internal needs that evolve each step
- Behavior is driven by which need is most pressing, not hardcoded rules
- Wolves balance hunting vs fleeing vs resting based on internal state
- Sheep balance grazing vs fleeing vs resting based on internal state

Friction points documented inline with # FRICTION comments.
"""

from mesa.discrete_space import CellAgent, FixedAgent


class NeedsBasedAnimal(CellAgent):
    """Base animal with continuous internal states driving behavior.

    Internal states (all floats 0.0-1.0):
        hunger: Increases each step. Reduced by eating.
        fear: Spikes when predators are nearby. Decays when safe.
        fatigue: Increases with movement, decreases with rest.
    """

    def __init__(
        self,
        model,
        energy=8,
        p_reproduce=0.04,
        energy_from_food=4,
        cell=None,
    ):
        super().__init__(model)
        self.energy = energy
        self.p_reproduce = p_reproduce
        self.energy_from_food = energy_from_food
        self.cell = cell

        # Continuous internal states (needs)
        self.hunger = 0.0
        self.fear = 0.0
        self.fatigue = 0.0

        # Tracking for analysis
        self.last_action = "idle"

    def _update_needs(self):
        """Evolve internal states based on current situation.

        # FRICTION: Mesa has no built-in "continuous state" abstraction.
        # We manually update floats each step. There's no way to say
        # "hunger increases at rate 0.05/tick" declaratively, nor to
        # trigger an event when hunger crosses a threshold (e.g., 0.8).
        # Discussion #2529 proposes exactly this — ContinuousState with
        # rate-of-change and threshold events.
        """
        # Hunger increases each step, proportional to missing energy
        max_energy = 20.0
        self.hunger = min(1.0, max(0.0, 1.0 - (self.energy / max_energy)))

        # Fatigue increases slightly each step, more if moved last step
        if self.last_action in ("flee", "hunt", "graze", "explore"):
            self.fatigue = min(1.0, self.fatigue + 0.08)
        else:
            self.fatigue = max(0.0, self.fatigue - 0.15)

        # Fear: computed from nearby threats (subclass-specific)
        self.fear = self._compute_fear()

    def _compute_fear(self):
        """Compute fear level from nearby threats. Override in subclass."""
        return 0.0

    def _decide(self):
        """Select action based on which need is most pressing.

        This is the core needs-based decision mechanism: the highest
        need wins. Ties broken by priority order: fear > hunger > fatigue.
        """
        needs = {
            "flee": self.fear,
            "eat": self.hunger,
            "rest": self.fatigue,
            "explore": 0.15,  # Base exploration drive
        }
        return max(needs, key=needs.get)

    def _act_flee(self):
        """Move away from threats."""
        self.last_action = "flee"
        self.energy -= 1.5  # Fleeing costs more energy
        self.cell = self.cell.neighborhood.select_random_cell()

    def _act_rest(self):
        """Stay in place, recover fatigue."""
        self.last_action = "rest"
        self.fatigue = max(0.0, self.fatigue - 0.3)
        self.energy -= 0.3  # Resting costs minimal energy

    def _act_explore(self):
        """Move randomly."""
        self.last_action = "explore"
        self.energy -= 1
        self.cell = self.cell.neighborhood.select_random_cell()

    def _act_eat(self):
        """Try to eat. Subclass implements specifics."""
        raise NotImplementedError

    def spawn_offspring(self):
        """Create offspring with inherited energy."""
        self.energy /= 2
        self.__class__(
            self.model,
            self.energy,
            self.p_reproduce,
            self.energy_from_food,
            self.cell,
        )

    def step(self):
        """Execute one step: update needs, decide, act, check survival."""
        self._update_needs()

        # Needs-based decision
        action = self._decide()

        if action == "flee":
            self._act_flee()
        elif action == "eat":
            self._act_eat()
        elif action == "rest":
            self._act_rest()
        else:
            self._act_explore()

        # Death check
        if self.energy < 0:
            self.remove()
            return

        # Reproduction (same as core Wolf-Sheep)
        if self.random.random() < self.p_reproduce:
            self.spawn_offspring()


class NeedsSheep(NeedsBasedAnimal):
    """A sheep with needs-based behavior.

    Behavior priorities:
    - High fear → flee from wolves
    - High hunger → seek and eat grass
    - High fatigue → rest in place
    - Otherwise → explore randomly
    """

    def _compute_fear(self):
        """Fear based on nearby wolves."""
        # FRICTION: self.cell.neighborhood returns a CellCollection.
        # To count wolves, we iterate over all neighboring cells and
        # their agents. There's no built-in "count agents of type X
        # within radius R" — you compose it from neighborhood + select.
        # This works but is verbose for a very common operation.
        wolf_count = 0
        for cell in self.cell.neighborhood:
            for agent in cell.agents:
                if isinstance(agent, NeedsWolf):
                    wolf_count += 1

        # Fear scales with wolf proximity — 1 wolf = 0.4, 2+ = near max
        return min(1.0, wolf_count * 0.4)

    def _act_eat(self):
        """Try to eat grass at current location, or move toward grass."""
        self.last_action = "graze"
        grass = next(
            (obj for obj in self.cell.agents if isinstance(obj, NeedsGrass)),
            None,
        )
        if grass is not None and grass.fully_grown:
            self.energy += self.energy_from_food
            grass.get_eaten()
            self.hunger = max(0.0, self.hunger - 0.3)
        else:
            # No grass here — move toward grass
            cells_with_grass = []
            for cell in self.cell.neighborhood:
                for agent in cell.agents:
                    if isinstance(agent, NeedsGrass) and agent.fully_grown:
                        cells_with_grass.append(cell)
                        break

            if cells_with_grass:
                self.cell = self.random.choice(cells_with_grass)
            else:
                self.cell = self.cell.neighborhood.select_random_cell()
            self.energy -= 1

    def _act_flee(self):
        """Move away from wolves — prefer cells without wolves."""
        self.last_action = "flee"
        self.energy -= 1.5

        safe_cells = []
        for cell in self.cell.neighborhood:
            has_wolf = any(isinstance(a, NeedsWolf) for a in cell.agents)
            if not has_wolf:
                safe_cells.append(cell)

        if safe_cells:
            self.cell = self.random.choice(safe_cells)
        else:
            # Surrounded — move randomly
            self.cell = self.cell.neighborhood.select_random_cell()


class NeedsWolf(NeedsBasedAnimal):
    """A wolf with needs-based behavior.

    Behavior priorities:
    - High hunger → hunt for sheep
    - High fatigue → rest to recover
    - Otherwise → explore territory

    Wolves have low base fear (apex predator), but fear increases
    slightly when energy is critically low (desperation).
    """

    def _compute_fear(self):
        """Wolves fear starvation, not other agents."""
        if self.energy < 3:
            return 0.3  # Desperate — triggers erratic behavior
        return 0.0

    def _act_eat(self):
        """Hunt: move toward sheep and try to eat one."""
        self.last_action = "hunt"

        # Check current cell for sheep
        sheep_here = [obj for obj in self.cell.agents if isinstance(obj, NeedsSheep)]
        if sheep_here:
            target = self.random.choice(sheep_here)
            self.energy += self.energy_from_food
            target.remove()
            self.hunger = max(0.0, self.hunger - 0.5)
            return

        # No sheep here — move toward sheep
        # FRICTION: There's no built-in "find nearest agent of type X"
        # utility. We scan neighborhood manually. For larger search
        # radii this would need nested loops or a spatial query API.
        cells_with_sheep = []
        for cell in self.cell.neighborhood:
            if any(isinstance(a, NeedsSheep) for a in cell.agents):
                cells_with_sheep.append(cell)

        if cells_with_sheep:
            self.cell = self.random.choice(cells_with_sheep)
        else:
            self.cell = self.cell.neighborhood.select_random_cell()
        self.energy -= 1

    def _act_flee(self):
        """When desperate (low energy), move erratically."""
        self.last_action = "flee"
        self.energy -= 1
        self.cell = self.cell.neighborhood.select_random_cell()


class NeedsGrass(FixedAgent):
    """Grass patch — identical to core Wolf-Sheep."""

    def __init__(self, model, countdown, grass_regrowth_time, cell):
        super().__init__(model)
        self._fully_grown = countdown == 0
        self.grass_regrowth_time = grass_regrowth_time
        self.cell = cell

        if not self._fully_grown:
            self.model.simulator.schedule_event_relative(
                setattr, countdown, function_args=[self, "fully_grown", True]
            )

    @property
    def fully_grown(self):
        """Whether the grass patch is fully grown."""
        return self._fully_grown

    @fully_grown.setter
    def fully_grown(self, value: bool) -> None:
        """Set grass growth state and schedule regrowth if eaten."""
        self._fully_grown = value

        if not value:
            self.model.simulator.schedule_event_relative(
                setattr,
                self.grass_regrowth_time,
                function_args=[self, "fully_grown", True],
            )

    def get_eaten(self):
        self.fully_grown = False
