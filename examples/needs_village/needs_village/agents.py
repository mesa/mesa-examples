"""
agents.py — Agents for the Needs-Based Village model.

Provides:
  NeedSpec      — configuration dataclass for one homeostatic need
  NeedsAgent    — abstract CellAgent driven by competing needs
  FoodSource    — stationary food patch (regenerates 1 unit/step)
  HomePatch     — stationary rest site
  ThreatAgent   — roaming predator that spikes nearby SAFETY need
  VillagerAgent — concrete NeedsAgent with HUNGER / REST / SOCIAL / SAFETY
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from mesa.discrete_space import CellAgent


# ──────────────────────────────────────────────────────────────────────── #
#  NeedsAgent base class                                                   #
# ──────────────────────────────────────────────────────────────────────── #


@dataclass
class NeedSpec:
    """Configuration for a single homeostatic need.

    Parameters
    ----------
    name:
        Identifier used as the dict key in NeedsAgent.needs.
    decay_rate:
        Autonomous urgency growth per step (0 = perception-only).
    critical_threshold:
        Level above which the need is considered urgent.
    satisfy_amount:
        How much one satisfying action reduces the need.
    """

    name: str
    decay_rate: float
    critical_threshold: float = 0.75
    satisfy_amount: float = 0.40


class NeedsAgent(CellAgent, ABC):
    """Abstract CellAgent driven by competing homeostatic needs.

    Each step:
      1. ``perceive()``         — update needs from the environment
      2. ``_decay_needs()``     — autonomous urgency growth
      3. ``most_urgent_need()`` — select highest-urgency need
      4. preemption check       — increment counter if priority shifted
      5. ``act_on_need()``      — execute one action for the selected need

    Subclasses must implement ``act_on_need(need_name)``.
    Subclasses may override ``perceive()`` (default: no-op).

    Attributes
    ----------
    needs : dict[str, float]
        Current urgency per need (0.0 satisfied → 1.0 critical).
    _active_need : str | None
        The need addressed this step.
    _preemption_count : int
        Times the priority order changed while a need was active.
        Demonstrates Pain Point #16: Mesa has no hook for preemption events.
    """

    def __init__(self, model, need_specs: list[NeedSpec]) -> None:
        super().__init__(model)
        self._specs: dict[str, NeedSpec] = {s.name: s for s in need_specs}
        self.needs: dict[str, float] = {s.name: 0.0 for s in need_specs}
        self._active_need: str | None = None
        self._preemption_count: int = 0

    def _decay_needs(self) -> None:
        for name, spec in self._specs.items():
            self.needs[name] = min(1.0, self.needs[name] + spec.decay_rate)

    def most_urgent_need(self) -> str:
        return max(self.needs, key=lambda n: self.needs[n])

    def satisfy(self, need_name: str) -> None:
        spec = self._specs[need_name]
        self.needs[need_name] = max(0.0, self.needs[need_name] - spec.satisfy_amount)

    def in_critical_state(self) -> bool:
        return any(
            self.needs[n] >= s.critical_threshold for n, s in self._specs.items()
        )

    def perceive(self) -> None:
        """Override to update needs from the environment before decay."""

    @abstractmethod
    def act_on_need(self, need_name: str) -> None:
        """Execute one atomic action to address *need_name*."""

    def step(self) -> None:
        self.perceive()
        self._decay_needs()
        urgent = self.most_urgent_need()
        # Pain Point #16: no Mesa hook to interrupt in-progress actions
        if self._active_need is not None and urgent != self._active_need:
            self._preemption_count += 1
        self._active_need = urgent
        self.act_on_need(urgent)


# ──────────────────────────────────────────────────────────────────────── #
#  Environment agents                                                      #
# ──────────────────────────────────────────────────────────────────────── #


class FoodSource(CellAgent):
    """Stationary food patch.  Regenerates 1 food unit per step up to MAX_FOOD."""

    MAX_FOOD: int = 6

    def __init__(self, model) -> None:
        super().__init__(model)
        self.food: int = self.MAX_FOOD

    def step(self) -> None:
        if self.food < self.MAX_FOOD:
            self.food += 1

    @property
    def depleted(self) -> bool:
        return self.food == 0


class HomePatch(CellAgent):
    """Stationary rest site.  Villagers satisfy REST by standing adjacent."""

    def __init__(self, model) -> None:
        super().__init__(model)

    def step(self) -> None:
        pass


class ThreatAgent(CellAgent):
    """Roaming predator.  Performs a random walk; spikes nearby SAFETY need."""

    def __init__(self, model) -> None:
        super().__init__(model)

    def step(self) -> None:
        self.cell = self.cell.neighborhood.select_random_cell()


# ──────────────────────────────────────────────────────────────────────── #
#  Villager agent                                                          #
# ──────────────────────────────────────────────────────────────────────── #

_THREAT_RADIUS: int = 3

_VILLAGER_SPECS: list[NeedSpec] = [
    NeedSpec("HUNGER", decay_rate=0.045, critical_threshold=0.75, satisfy_amount=0.55),
    NeedSpec("REST",   decay_rate=0.030, critical_threshold=0.80, satisfy_amount=0.65),
    NeedSpec("SOCIAL", decay_rate=0.020, critical_threshold=0.70, satisfy_amount=0.35),
    # SAFETY has zero autonomous decay; it is driven entirely by perception.
    NeedSpec("SAFETY", decay_rate=0.000, critical_threshold=0.60, satisfy_amount=1.00),
]


class VillagerAgent(NeedsAgent):
    """Homeostatic villager with four competing needs.

    Decision cycle (each step)
    --------------------------
    perceive()        scans for nearby ThreatAgents; spikes/dissipates SAFETY
    _decay_needs()    advances HUNGER, REST, SOCIAL autonomously
    most_urgent_need  selects the highest-urgency need
    act_on_need       moves toward the relevant resource and satisfies on arrival

    Architectural contrast with BDI agents
    ---------------------------------------
    BDI agents hold explicit goals that pull them toward desired states.
    Villagers are *pushed* by drives that grow autonomously and are never
    fully extinguished — only temporarily suppressed.  Priority is dynamic
    and can preempt in-progress movement (Pain Point #16).
    """

    def __init__(self, model) -> None:
        super().__init__(model, list(_VILLAGER_SPECS))

    # ------------------------------------------------------------------ #
    #  perceive: update SAFETY from environment                          #
    # ------------------------------------------------------------------ #

    def perceive(self) -> None:
        """Spike SAFETY when a ThreatAgent is within _THREAT_RADIUS cells.

        Pain Point #10 (revisited): Mesa offers no typed-radius query.
        We compute Manhattan distances to all ThreatAgents manually.
        """
        threats = list(self.model.agents_by_type.get(ThreatAgent, []))
        my_x, my_y = self.cell.coordinate
        threat_nearby = any(
            abs(t.cell.coordinate[0] - my_x) + abs(t.cell.coordinate[1] - my_y)
            <= _THREAT_RADIUS
            for t in threats
        )
        if threat_nearby:
            self.needs["SAFETY"] = min(1.0, self.needs["SAFETY"] + 0.50)
        else:
            self.needs["SAFETY"] = max(0.0, self.needs["SAFETY"] - 0.12)

    # ------------------------------------------------------------------ #
    #  Movement helpers                                                   #
    # ------------------------------------------------------------------ #

    def _step_toward(self, target_cell) -> None:
        """Move one cell toward *target_cell* using greedy Manhattan step."""
        my_x, my_y = self.cell.coordinate
        tx, ty = target_cell.coordinate
        dx = 0 if tx == my_x else (1 if tx > my_x else -1)
        dy = 0 if ty == my_y else (1 if ty > my_y else -1)
        new_x = (my_x + dx) % self.model.width
        new_y = (my_y + dy) % self.model.height
        self.move_to(self.model.grid[(new_x, new_y)])

    def _nearest(self, agent_type: type):
        """Return the closest agent of *agent_type* by Manhattan distance."""
        # Pain Point #11: agents_by_type[T] raises KeyError if T was
        # fully removed; .get() is the safe workaround.
        pool = [
            a for a in self.model.agents_by_type.get(agent_type, [])
            if a.cell is not None
        ]
        if not pool:
            return None
        my_x, my_y = self.cell.coordinate
        return min(
            pool,
            key=lambda a: abs(a.cell.coordinate[0] - my_x) + abs(a.cell.coordinate[1] - my_y),
        )

    def _adjacent_to(self, other_cell) -> bool:
        ox, oy = other_cell.coordinate
        my_x, my_y = self.cell.coordinate
        return abs(ox - my_x) <= 1 and abs(oy - my_y) <= 1

    # ------------------------------------------------------------------ #
    #  act_on_need: NeedsAgent abstract method                           #
    # ------------------------------------------------------------------ #

    def act_on_need(self, need_name: str) -> None:
        if need_name == "SAFETY":
            self._act_safety()
        elif need_name == "HUNGER":
            self._act_hunger()
        elif need_name == "REST":
            self._act_rest()
        elif need_name == "SOCIAL":
            self._act_social()

    def _act_safety(self) -> None:
        threat = self._nearest(ThreatAgent)
        if threat is None:
            return
        # Move away from threat
        my_x, my_y = self.cell.coordinate
        tx, ty = threat.cell.coordinate
        dx = 0 if tx == my_x else (1 if my_x > tx else -1)
        dy = 0 if ty == my_y else (1 if my_y > ty else -1)
        new_x = (my_x + dx) % self.model.width
        new_y = (my_y + dy) % self.model.height
        self.move_to(self.model.grid[(new_x, new_y)])

    def _act_hunger(self) -> None:
        food = self._nearest(FoodSource)
        if food is None:
            self.cell = self.cell.neighborhood.select_random_cell()
            return
        if self._adjacent_to(food.cell) or self.cell is food.cell:
            if not food.depleted:
                food.food -= 1
                self.satisfy("HUNGER")
                # Incidental social contact during a shared meal
                if any(isinstance(a, VillagerAgent) for a in self.cell.neighborhood.agents):
                    self.needs["SOCIAL"] = max(0.0, self.needs["SOCIAL"] - 0.08)
        else:
            self._step_toward(food.cell)

    def _act_rest(self) -> None:
        home = self._nearest(HomePatch)
        if home is None:
            self.cell = self.cell.neighborhood.select_random_cell()
            return
        if self._adjacent_to(home.cell) or self.cell is home.cell:
            self.satisfy("REST")
        else:
            self._step_toward(home.cell)

    def _act_social(self) -> None:
        """Seek the nearest villager; mutually satisfy SOCIAL on arrival."""
        others = [
            a for a in self.model.agents_by_type.get(VillagerAgent, [])
            if a is not self
        ]
        if not others:
            self.cell = self.cell.neighborhood.select_random_cell()
            return
        my_x, my_y = self.cell.coordinate
        partner = min(
            others,
            key=lambda a: abs(a.cell.coordinate[0] - my_x) + abs(a.cell.coordinate[1] - my_y),
        )
        if self._adjacent_to(partner.cell) or self.cell is partner.cell:
            self.satisfy("SOCIAL")
            partner.satisfy("SOCIAL")   # mutual satisfaction
        else:
            self._step_toward(partner.cell)

    # ------------------------------------------------------------------ #
    #  Pain Point #17: state discretisation helper for RL integration    #
    # ------------------------------------------------------------------ #

    def discretise_needs(self, buckets: int = 3) -> tuple[int, ...]:
        """Bucket continuous need floats into discrete integers.

        Pain Point #17: Mesa provides no built-in feature-engineering
        utility. With 4 needs × 3 buckets = 81 discrete states; including
        position on a 25×25 grid gives 81 × 625 = 50 625 states.
        """
        step = 1.0 / buckets
        return tuple(min(buckets - 1, int(v / step)) for v in self.needs.values())
