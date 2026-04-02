"""Dormant Alliances Model — Mesa meta-agent lifecycle demonstration.

This model shows how the new MetaAgent lifecycle features (GSoC 2026) work
in a realistic simulation:

  - Countries gain and lose power each step.
  - Countries with compatible power levels form alliances (MetaAgents).
  - When an alliance loses >50% of its founding members it goes DORMANT.
  - A dormant alliance can be reactivated if its remaining members recruit
    enough new countries.
  - When all members are gone the alliance is DISSOLVED.

Run with:
    solara run app.py
Or headless:
    python model.py
"""

from __future__ import annotations

import mesa

from .agents import Alliance, CountryAgent
from mesa.experimental.meta_agents import create_meta_agent


# Minimum combined power for two countries to consider forming an alliance
ALLIANCE_FORMATION_THRESHOLD = 40.0

# How often (in steps) dormant alliances attempt to recruit and reactivate
REACTIVATION_INTERVAL = 5


class DormantAlliancesModel(mesa.Model):
    """Agent-based model demonstrating MetaAgent lifecycle management.

    Parameters
    ----------
    n_countries : int
        Number of country agents to create. Default 20.
    alliance_threshold : float
        Minimum *combined* power required to form a new alliance.
    reactivation_interval : int
        How many steps between dormant-alliance reactivation attempts.
    seed : int | None
        Random seed for reproducibility.
    """

    def __init__(
        self,
        n_countries: int = 20,
        alliance_threshold: float = ALLIANCE_FORMATION_THRESHOLD,
        reactivation_interval: int = REACTIVATION_INTERVAL,
        seed: int | None = 42,
    ):
        super().__init__(seed=seed)

        self.alliance_threshold = alliance_threshold
        self.reactivation_interval = reactivation_interval

        # Create countries
        for _ in range(n_countries):
            CountryAgent(self)

        # Collect a snapshot of active/dormant alliances each step
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Active Alliances":   lambda m: m._count_alliances("ACTIVE"),
                "Dormant Alliances":  lambda m: m._count_alliances("DORMANT"),
                "Total Countries":    lambda m: len(m.agents_by_type.get(CountryAgent, [])),
                "Mean Country Power": lambda m: m._mean_power(),
            },
            agent_reporters={
                "Power":    lambda a: getattr(a, "power", None),
                "Defeated": lambda a: getattr(a, "defeated", None),
            },
        )

        # Form initial alliances
        self._form_alliances()

    # ------------------------------------------------------------------
    # DataCollector helpers
    # ------------------------------------------------------------------

    def _count_alliances(self, state_name: str) -> int:
        alliances = self.agents_by_type.get(Alliance, [])
        return sum(1 for a in alliances if a.state.name == state_name)

    def _mean_power(self) -> float:
        countries = list(self.agents_by_type.get(CountryAgent, []))
        if not countries:
            return 0.0
        return sum(c.power for c in countries) / len(countries)

    # ------------------------------------------------------------------
    # Alliance formation logic
    # ------------------------------------------------------------------

    def _form_alliances(self) -> None:
        """Pair up unaffiliated countries whose combined power exceeds the
        threshold and create a new Alliance MetaAgent for each eligible pair.
        """
        unaffiliated = [
            c for c in self.agents_by_type.get(CountryAgent, [])
            if c.alliance is None
        ]
        self.rng.shuffle(unaffiliated)

        i = 0
        while i + 1 < len(unaffiliated):
            c1, c2 = unaffiliated[i], unaffiliated[i + 1]
            if c1.power + c2.power >= self.alliance_threshold:
                alliance = create_meta_agent(
                    model=self,
                    new_agent_class="Alliance",
                    agents=[c1, c2],
                    mesa_agent_type=Alliance,
                    meta_attributes={"power_threshold": self.alliance_threshold},
                )
                # Optionally log the formation
                print(f"  ✦ Formed {alliance}")
                i += 2
            else:
                i += 1

    def _try_reactivate_dormant(self) -> None:
        """Attempt to grow dormant alliances by recruiting unaffiliated countries.

        If a dormant alliance can recruit enough members to exceed half its
        founding size, it reactivates.
        """
        dormant = [
            a for a in self.agents_by_type.get(Alliance, [])
            if a.is_dormant
        ]
        unaffiliated = [
            c for c in self.agents_by_type.get(CountryAgent, [])
            if c.alliance is None
        ]

        for alliance in dormant:
            # How many new recruits are needed to exceed founding_size / 2?
            needed = max(0, int(alliance.founding_size / 2) + 1 - alliance.size)
            recruits = unaffiliated[:needed]

            if len(recruits) >= needed and needed > 0:
                alliance.add_constituting_agents(set(recruits))
                for r in recruits:
                    unaffiliated.remove(r)
                alliance.activate()
                print(
                    f"  ✦ Reactivated {alliance} "
                    f"(recruited {len(recruits)} new members)"
                )

    # ------------------------------------------------------------------
    # Model step
    # ------------------------------------------------------------------

    def step(self) -> None:
        """Advance the model by one tick.

        Order of operations:
        1. Active alliances step (which cascades to their member countries).
        2. Unaffiliated countries step independently.
        3. Periodically attempt dormant-alliance reactivation.
        4. Form new alliances among any newly unaffiliated countries.
        5. Collect data.
        """
        stepped_country_ids: set[int] = set()

        # 1. Step active alliances (cascade reaches member countries)
        for alliance in list(self.agents_by_type.get(Alliance, [])):
            if alliance.is_active:
                alliance.step()
                for member in list(alliance.agents):
                    stepped_country_ids.add(member.unique_id)

        # 2. Step unaffiliated countries (not yet stepped this tick)
        for country in list(self.agents_by_type.get(CountryAgent, [])):
            if country.unique_id not in stepped_country_ids:
                country.step()

        # 3. Periodically attempt reactivation
        if self.time % self.reactivation_interval == 0:
            self._try_reactivate_dormant()

        # 4. Try to form new alliances
        self._form_alliances()

        # 5. Collect data
        self.datacollector.collect(self)


# ---------------------------------------------------------------------------
# Headless run (python model.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Dormant Alliances Model ===\n")
    model = DormantAlliancesModel(n_countries=20, seed=42)

    for step in range(30):
        print(f"\n--- Step {step + 1} ---")
        model.step()
        df = model.datacollector.get_model_vars_dataframe()
        last = df.iloc[-1]
        print(
            f"  Countries: {int(last['Total Countries'])}  "
            f"Active alliances: {int(last['Active Alliances'])}  "
            f"Dormant: {int(last['Dormant Alliances'])}  "
            f"Mean power: {last['Mean Country Power']:.1f}"
        )

    print("\n=== Final Alliance Snapshots ===")
    for alliance in model.agents_by_type.get(Alliance, []):
        print(" ", alliance.to_dict())

