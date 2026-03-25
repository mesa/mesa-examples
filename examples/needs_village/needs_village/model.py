"""
model.py — VillageModel: needs-based homeostatic agents on an OrthogonalMooreGrid.

N villagers manage four competing needs (HUNGER, REST, SOCIAL, SAFETY).
At every step each villager acts on whichever need is most urgent.

This model demonstrates the NeedsAgent architecture: a third decision-making
paradigm alongside reactive agents and BDI deliberation.  Needs are
*pushed* by autonomous decay; they can only be suppressed, never eliminated.

Pain Points Surfaced
--------------------
#16 (High)   No preemption hook — priority flips are counted via
             _preemption_count but Mesa has no on_preempt() callback.
#17 (Medium) Continuous need floats are poor RL state variables; see
             VillagerAgent.discretise_needs() for the manual overhead.
#18 (Medium) DataCollector records snapshots only; the integral metric
             "agent-steps in critical state" needs a manual accumulator.
"""

from __future__ import annotations

import mesa
from mesa.discrete_space import OrthogonalMooreGrid

from .agents import FoodSource, HomePatch, ThreatAgent, VillagerAgent


def _mean_need(model: VillageModel, need_name: str) -> float:
    villagers = list(model.agents_by_type.get(VillagerAgent, []))
    if not villagers:
        return 0.0
    return sum(a.needs[need_name] for a in villagers) / len(villagers)


def _count_driven_by(model: VillageModel, need_name: str) -> int:
    return sum(
        1
        for a in model.agents_by_type.get(VillagerAgent, [])
        if a._active_need == need_name
    )


class VillageModel(mesa.Model):
    """Homeostatic village: N villagers manage four competing needs on a grid.

    Parameters
    ----------
    n_villagers : int
        Number of VillagerAgent instances.
    n_food : int
        Number of FoodSource patches.
    n_homes : int
        Number of HomePatch rest sites.
    n_threats : int
        Number of ThreatAgent roaming predators.
    width, height : int
        Grid dimensions.
    rng : int | None
        Random seed for reproducibility.
    """

    def __init__(
        self,
        n_villagers: int = 20,
        n_food: int = 8,
        n_homes: int = 5,
        n_threats: int = 2,
        width: int = 25,
        height: int = 25,
        rng=None,
    ) -> None:
        super().__init__(rng=rng)
        self.width = width
        self.height = height
        self.grid = OrthogonalMooreGrid((width, height), torus=True, random=self.random)

        # Distribute agents across distinct cells for initial placement
        all_cells = list(self.grid.all_cells)
        self.random.shuffle(all_cells)
        idx = 0

        for _ in range(n_food):
            FoodSource(self).move_to(all_cells[idx])
            idx += 1
        for _ in range(n_homes):
            HomePatch(self).move_to(all_cells[idx])
            idx += 1
        for _ in range(n_threats):
            ThreatAgent(self).move_to(all_cells[idx])
            idx += 1
        for _ in range(n_villagers):
            VillagerAgent(self).move_to(all_cells[idx])
            idx += 1

        # Manual accumulator for Pain Point #18:
        # DataCollector cannot express ∫ critical_agents dt
        self._critical_steps: int = 0

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "MeanHunger": lambda m: _mean_need(m, "HUNGER"),
                "MeanRest": lambda m: _mean_need(m, "REST"),
                "MeanSocial": lambda m: _mean_need(m, "SOCIAL"),
                "MeanSafety": lambda m: _mean_need(m, "SAFETY"),
                "CriticalAgents": lambda m: sum(
                    1
                    for a in m.agents_by_type.get(VillagerAgent, [])
                    if a.in_critical_state()
                ),
                # Pain Point #16: cumulative preemption events
                "TotalPreemptions": lambda m: sum(
                    a._preemption_count for a in m.agents_by_type.get(VillagerAgent, [])
                ),
                # Pain Point #18: integral metric via manual accumulator
                "CumulativeCriticalSteps": lambda m: m._critical_steps,
                "DrivenByHunger": lambda m: _count_driven_by(m, "HUNGER"),
                "DrivenByRest": lambda m: _count_driven_by(m, "REST"),
                "DrivenBySocial": lambda m: _count_driven_by(m, "SOCIAL"),
                "DrivenBySafety": lambda m: _count_driven_by(m, "SAFETY"),
            },
            agent_reporters={
                "Hunger": lambda a: a.needs.get("HUNGER")
                if isinstance(a, VillagerAgent)
                else None,
                "Rest": lambda a: a.needs.get("REST")
                if isinstance(a, VillagerAgent)
                else None,
                "Social": lambda a: a.needs.get("SOCIAL")
                if isinstance(a, VillagerAgent)
                else None,
                "Safety": lambda a: a.needs.get("SAFETY")
                if isinstance(a, VillagerAgent)
                else None,
                "ActiveNeed": lambda a: a._active_need
                if isinstance(a, VillagerAgent)
                else None,
                "Preemptions": lambda a: a._preemption_count
                if isinstance(a, VillagerAgent)
                else None,
            },
        )

    def step(self) -> None:
        # Accumulate integral metric before stepping (Pain Point #18)
        self._critical_steps += sum(
            1
            for a in self.agents_by_type.get(VillagerAgent, [])
            if a.in_critical_state()
        )
        # Stepping order: threats move first so villagers perceive current positions
        self.agents_by_type[ThreatAgent].shuffle_do("step")
        self.agents_by_type[FoodSource].shuffle_do("step")
        self.agents_by_type[VillagerAgent].shuffle_do("step")
        self.datacollector.collect(self)
