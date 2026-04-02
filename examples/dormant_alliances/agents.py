"""Agent definitions for the Dormant Alliances model.

This model extends the classic Alliance Formation concept to demonstrate
the new MetaAgent lifecycle features added in the GSoC 2026 contribution:

  - MetaAgentState (ACTIVE / DORMANT / DISSOLVED)
  - activate() / deactivate() lifecycle transitions
  - Signal / event system (on / emit)
  - cascade_step for automatic member stepping
  - to_dict() serialisation
"""

from __future__ import annotations

import mesa
from mesa.experimental.meta_agents import MetaAgent


# ---------------------------------------------------------------------------
# Country agent
# ---------------------------------------------------------------------------

class CountryAgent(mesa.Agent):
    """A country that can join alliances, gain/lose power, and be defeated.

    Attributes:
        power:      Current military/economic power (float, 0–100).
        defeated:   True once power drops to 0 and the country is removed.
    """

    def __init__(self, model: mesa.Model, power: float | None = None):
        super().__init__(model)
        self.power: float = power if power is not None else model.rng.uniform(10, 100)
        self.defeated: bool = False

    # ------------------------------------------------------------------
    # Properties used by the model to inspect state
    # ------------------------------------------------------------------

    @property
    def alliance(self) -> "Alliance | None":
        """Convenience accessor: the first Alliance this country belongs to."""
        if hasattr(self, "meta_agents"):
            alliances = [ma for ma in self.meta_agents if isinstance(ma, Alliance)]
            return alliances[0] if alliances else None
        return None

    # ------------------------------------------------------------------
    # Step
    # ------------------------------------------------------------------

    def step(self) -> None:
        """Each tick a country loses a small random amount of power.

        If power hits zero it emits ``"member_defeated"`` on its alliance
        (demonstrating the signal system) and removes itself.
        """
        if self.defeated:
            return

        # Lose 1–8 power per step
        loss = self.model.rng.uniform(1, 8)
        self.power = max(0.0, self.power - loss)

        if self.power == 0.0:
            self.defeated = True
            # Signal the alliance (if any) before removing self
            if self.alliance is not None:
                self.alliance.emit("member_defeated", self)
            self.remove()

    def __repr__(self) -> str:
        return f"<Country id={self.unique_id} power={self.power:.1f}>"


# ---------------------------------------------------------------------------
# Alliance meta-agent
# ---------------------------------------------------------------------------

class Alliance(MetaAgent):
    """A group of countries that act as a collective entity.

    Demonstrates every new MetaAgent feature:

    1. **Lifecycle** — deactivates (goes DORMANT) when the alliance loses
       more than half its founding members; reactivates when it recruits
       enough new members to recover.

    2. **Signals** — listens for ``"member_defeated"`` from each country and
       calls ``_on_member_defeated``.  Also emits ``"alliance_weakened"``
       when total power drops below the configured threshold.

    3. **cascade_step** — set to True so Alliance.step() automatically
       steps all member countries after its own logic, removing the need
       for boilerplate in the model.

    4. **to_dict** — used by the DataCollector for structured logging.

    Attributes:
        founding_size:     Number of members at formation.
        power_threshold:   Minimum combined power before "weakened" is fired.
        _weakened_emitted: Guard so the signal fires only once.
    """

    cascade_step: bool = True   # automatically step all members

    def __init__(
        self,
        model: mesa.Model,
        agents: set[CountryAgent] | None = None,
        name: str = "Alliance",
        *,
        power_threshold: float = 50.0,
    ):
        super().__init__(model, agents, name)

        self.founding_size: int = len(self._constituting_set)
        self.power_threshold: float = power_threshold
        self._weakened_emitted: bool = False

        # Register signal handler: react when a member is defeated
        self.on("member_defeated", self._on_member_defeated)

    # ------------------------------------------------------------------
    # Computed properties
    # ------------------------------------------------------------------

    @property
    def total_power(self) -> float:
        """Sum of power across all active member countries."""
        return sum(a.power for a in self._constituting_set)

    @property
    def size(self) -> int:
        """Current number of members."""
        return len(self._constituting_set)

    # ------------------------------------------------------------------
    # Signal handlers
    # ------------------------------------------------------------------

    def _on_member_defeated(self, country: CountryAgent) -> None:
        """Called automatically when a member emits 'member_defeated'.

        Removes the country from the alliance and checks whether the group
        has shrunk below half its founding size — if so, deactivates.
        """
        self.remove_constituting_agents({country})

        if self.size == 0:
            # All members gone — dissolve entirely
            self.remove()
            return

        # Deactivate if we have lost more than half our founding members
        if self.is_active and self.size < self.founding_size / 2:
            self.deactivate()
            print(
                f"  ⚠ {self} lost majority of founders — going DORMANT "
                f"(founders={self.founding_size}, now={self.size})"
            )

    # ------------------------------------------------------------------
    # Step (meta-level logic runs BEFORE members, thanks to cascade_step)
    # ------------------------------------------------------------------

    def step(self) -> None:
        """Alliance-level logic: emit 'alliance_weakened' if power is low.

        Because ``cascade_step = True``, the base-class step() will call
        step() on every member country automatically after this method
        returns (handled in MetaAgent.step()).
        """
        if not self.is_active:
            return   # DORMANT — skip entirely; base class will also guard

        # Check collective power
        if (
            not self._weakened_emitted
            and self.total_power < self.power_threshold
        ):
            self._weakened_emitted = True
            self.emit("alliance_weakened", self)

        # Attempt to reactivate if previously dormant and now has enough members
        # (This branch is only reached if caller explicitly re-activates first.)

        # Delegate to parent, which cascades to members
        super().step()

    def __repr__(self) -> str:
        return (
            f"<Alliance {self.name!r} id={self.unique_id} "
            f"state={self._state.name} members={self.size} "
            f"power={self.total_power:.1f}>"
        )

