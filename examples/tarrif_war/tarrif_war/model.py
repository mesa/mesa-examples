import numpy as np
import mesa
from mesa import DataCollector

from .agent import State, Organization, Resident


class TariffWarModel(mesa.Model):
    """
    Global trade war simulation.

    Emergent phenomena:
      1. Step-wise government expansion (Higgs Ratchet Effect)
      2. Trade Diversion – Neutral Asia short-term gain, long-term loss
      3. Self-fulfilling recession spiral (CEE-SAC β turns negative)
      4. Resource misallocation → global GDP contraction
      5. Firm bankruptcy → unemployment → consumer welfare collapse
      6. Endogenous Interests Ratchet (lobbying locks in tariffs)
    """

    def __init__(
        self,
        n_firms_per_country: int = 6,
        n_residents_per_country: int = 8,
        retaliation_intensity: float = 0.08,
        lobbying_sensitivity: float = 0.25,
        expectation_adaptation_rate: float = 0.15,
        production_elasticity: float = 0.40,
        trade_stickiness: float = 0.40,
        base_global_demand: int = 100,
        global_crisis: bool = True,
        seed=42,
    ):
        super().__init__(seed=seed)
        self.n_firms_per_country = n_firms_per_country
        self.n_residents_per_country = n_residents_per_country
        self.base_global_demand = base_global_demand
        self.global_crisis = global_crisis
        self.countries = ["USA", "China", "Neutral Asia"]

        # ── Agents ─────────────────────────────────────────────────────────────
        for country in self.countries:
            s = State(
                self, country,
                retaliation_intensity=retaliation_intensity,
                lobbying_sensitivity=lobbying_sensitivity,
            )
            s.initialize_tariffs(self.countries)

        for country in self.countries:
            for _ in range(n_firms_per_country):
                Organization(
                    self, country,
                    trade_stickiness=trade_stickiness,
                    expectation_adaptation_rate=expectation_adaptation_rate,
                    production_elasticity=production_elasticity,
                )

        for country in self.countries:
            for _ in range(n_residents_per_country):
                Resident(self, country)

        # Bilateral trade flow matrix
        self.trade_flows = {
            (c1, c2): 0.0
            for c1 in self.countries for c2 in self.countries if c1 != c2
        }

        # ── DataCollector ──────────────────────────────────────────────────────
        self.datacollector = DataCollector(
            model_reporters={
                # ── GDP (total firm production by country) ──
                "USA_GDP": lambda m: sum(
                    o.production for o in m.agents_by_type[Organization]
                    if o.country == "USA"
                ),
                "China_GDP": lambda m: sum(
                    o.production for o in m.agents_by_type[Organization]
                    if o.country == "China"
                ),
                "NeutralAsia_GDP": lambda m: sum(
                    o.production for o in m.agents_by_type[Organization]
                    if o.country == "Neutral Asia"
                ),
                # ── Government size ratchet ──
                "Avg_Gov_Size": lambda m: float(
                    np.mean([s.gov_size for s in m.agents_by_type[State]])
                ),
                # ── Bilateral tariffs ──
                "USA_China_Tariff": lambda m: m._get_state("USA").get_tariff_to("China"),
                "China_USA_Tariff": lambda m: m._get_state("China").get_tariff_to("USA"),
                # ── Expectation gap (recession spiral) ──
                "Global_Expected_Demand": lambda m: float(
                    np.mean([o.expected_demand for o in m.agents_by_type[Organization]])
                ),
                "Global_Actual_Production": lambda m: float(
                    np.mean([o.production for o in m.agents_by_type[Organization]])
                ),
                # ── CEE-SAC β by country (< 0 = pessimism spiral) ──
                "Beta_USA": lambda m: float(
                    np.mean([o.beta for o in m.agents_by_type[Organization]
                              if o.country == "USA"])
                ),
                "Beta_China": lambda m: float(
                    np.mean([o.beta for o in m.agents_by_type[Organization]
                              if o.country == "China"])
                ),
                "Beta_Neutral": lambda m: float(
                    np.mean([o.beta for o in m.agents_by_type[Organization]
                              if o.country == "Neutral Asia"])
                ),
                # ── Lobbying power (endogenous ratchet) ──
                "Lobby_USA": lambda m: float(
                    np.mean([o.lobbying_power for o in m.agents_by_type[Organization]
                              if o.country == "USA"])
                ),
                "Lobby_China": lambda m: float(
                    np.mean([o.lobbying_power for o in m.agents_by_type[Organization]
                              if o.country == "China"])
                ),
                # ── Firm health: bankruptcy rate by country ──
                "Bankruptcy_USA": lambda m: _bankruptcy_rate(m, "USA"),
                "Bankruptcy_China": lambda m: _bankruptcy_rate(m, "China"),
                "Bankruptcy_Neutral": lambda m: _bankruptcy_rate(m, "Neutral Asia"),
                # ── Average firm profit by country ──
                "AvgProfit_USA": lambda m: _avg_profit(m, "USA"),
                "AvgProfit_China": lambda m: _avg_profit(m, "China"),
                "AvgProfit_Neutral": lambda m: _avg_profit(m, "Neutral Asia"),
                # ── Consumer welfare by country ──
                "Welfare_USA": lambda m: _avg_welfare(m, "USA"),
                "Welfare_China": lambda m: _avg_welfare(m, "China"),
                "Welfare_Neutral": lambda m: _avg_welfare(m, "Neutral Asia"),
                # ── Trade balance by country ──
                "TradeBalance_USA": lambda m: m._get_state("USA").trade_balance,
                "TradeBalance_China": lambda m: m._get_state("China").trade_balance,
                "TradeBalance_Neutral": lambda m: m._get_state("Neutral Asia").trade_balance,
            }
        )

        self._update_trade_flows()
        self.datacollector.collect(self)

    # ── helpers ────────────────────────────────────────────────────────────────

    def _get_state(self, country: str) -> State:
        for s in self.agents_by_type[State]:
            if s.country == country:
                return s
        raise ValueError(f"State not found: {country}")

    def _efficiency_for(self, country: str) -> float:
        """
        Country-specific efficiency multiplier.
        Countries directly targeted by high tariffs suffer more.
        Neutral Asia is largely spared; USA/China bear the brunt.
        """
        incoming = [
            s.get_tariff_to(country)
            for s in self.agents_by_type[State] if s.country != country
        ]
        avg_in = float(np.mean(incoming)) if incoming else 0.05
        # USA-China bilateral conflict creates global uncertainty for everyone
        usa_cn = self._get_state("USA").get_tariff_to("China")
        cn_usa = self._get_state("China").get_tariff_to("USA")
        conflict = (usa_cn + cn_usa) / 2.0
        return max(0.50, 1.0 - avg_in * 0.80 - conflict * 0.25)

    def get_demand_for(self, country: str) -> float:
        """
        Per-firm effective demand (zero-sum at global level):
          - incoming tariffs strongly reduce export attractiveness
          - trade diversion gives Neutral Asia a bounded share of USA/China losses
          - country-specific efficiency multiplier: targeted countries lose more
        """
        base = self.base_global_demand / len(self.countries)
        eff = self._efficiency_for(country)

        incoming = [
            s.get_tariff_to(country)
            for s in self.agents_by_type[State] if s.country != country
        ]
        avg_incoming = float(np.mean(incoming)) if incoming else 0.05

        diversion_bonus = 0.0
        if country == "Neutral Asia":
            usa_cn = self._get_state("USA").get_tariff_to("China")
            cn_usa = self._get_state("China").get_tariff_to("USA")
            usa_lost = usa_cn * base * 0.40
            cn_lost = cn_usa * base * 0.40
            diversion_bonus = (usa_lost + cn_lost) * 0.55

        foreign_residents = [
            r for r in self.agents_by_type[Resident] if r.country != country
        ]
        n_other = max(1, len(self.countries) - 1)
        consumer_cross = (
            sum(r.consumption * (1.0 - r.domestic_share) for r in foreign_residents)
            / n_other * 0.10
        )

        effective_demand = (
            base * (1.0 - avg_incoming * 0.80) + diversion_bonus + consumer_cross
        ) * eff

        return max(0.01, effective_demand / self.n_firms_per_country)

    def _update_trade_flows(self) -> None:
        """Recompute bilateral trade flow weights and each State's trade balance."""
        for (c_from, c_to) in self.trade_flows:
            orgs_from = [
                o for o in self.agents_by_type[Organization] if o.country == c_from
            ]
            s = self._get_state(c_from)
            tariff = s.get_tariff_to(c_to)
            raw = sum(o.production for o in orgs_from) * 0.35
            self.trade_flows[(c_from, c_to)] = max(0.0, raw * (1.0 - tariff * 0.90))

        # Update each country's trade balance
        for country in self.countries:
            s = self._get_state(country)
            s.exports = sum(
                self.trade_flows[(country, c)] for c in self.countries if c != country
            )
            s.imports = sum(
                self.trade_flows[(c, country)] for c in self.countries if c != country
            )
            s.trade_balance = s.exports - s.imports

    # ── main step ──────────────────────────────────────────────────────────────

    def step(self) -> None:
        self.agents_by_type[State].shuffle_do("step")
        self.agents_by_type[Organization].shuffle_do("step")
        self.agents_by_type[Resident].shuffle_do("step")
        self._update_trade_flows()
        self.datacollector.collect(self)


# ── module-level reporter helpers (avoids lambda closures capturing wrong vars) ──

def _bankruptcy_rate(model, country):
    firms = [o for o in model.agents_by_type[Organization] if o.country == country]
    if not firms:
        return 0.0
    return sum(1 for o in firms if o.bankrupt) / len(firms)


def _avg_profit(model, country):
    firms = [o for o in model.agents_by_type[Organization] if o.country == country]
    return float(np.mean([o.profit for o in firms])) if firms else 0.0


def _avg_welfare(model, country):
    residents = [r for r in model.agents_by_type[Resident] if r.country == country]
    return float(np.mean([r.welfare for r in residents])) if residents else 0.0
