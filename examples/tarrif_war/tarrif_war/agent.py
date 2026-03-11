import numpy as np
import mesa

# ── Sector parameters ──────────────────────────────────────────────────────────
# tariff_sens:   how much outgoing tariffs hurt this sector's exports
# lobby_eff:     how efficiently tariff rent converts to political influence
# prod_mult:     revenue price premium (sector quality/value-add multiplier)
#
# Real-world basis:
#   Tech:          high tariff sensitivity (supply chains), high lobbying (FAANG-style),
#                  premium pricing (>1.0 prod_mult)
#   Agriculture:   low tariff sensitivity domestically, very low lobbying efficiency,
#                  commodity pricing (<1.0 prod_mult) — hit hardest by retaliation
#   Manufacturing: moderate sensitivity, standard pricing
SECTOR_PARAMS = {
    "Tech":          {"tariff_sens": 1.4, "lobby_eff": 1.3, "prod_mult": 1.15},
    "Agriculture":   {"tariff_sens": 0.6, "lobby_eff": 0.7, "prod_mult": 0.85},
    "Manufacturing": {"tariff_sens": 1.0, "lobby_eff": 1.0, "prod_mult": 1.00},
}
SECTORS = list(SECTOR_PARAMS.keys())


class State(mesa.Agent):
    """
    Nation-state agent.

    Calibrated to 2018-2025 US-China trade war dynamics:
      - Baseline tariff ≈ 3% (WTO MFN average)
      - Peak tariff ≈ 25-35% (2018-2019 peak was ~25%; 2025 reached higher)
      - Escalation happens in rounds every ~2-3 months (modelled as cooldown=8 steps)
      - Government size baseline ≈ 20% of GDP (realistic for USA/China)
      - Ratchet: government expands +1.5 pp per escalation round, rarely shrinks
    """

    def __init__(self, model, country, retaliation_intensity=0.08, lobbying_sensitivity=0.25):
        super().__init__(model)
        self.country = country
        self.retaliation_intensity = retaliation_intensity
        self.lobbying_sensitivity = lobbying_sensitivity

        # Government size as % of GDP — USA ~21%, China ~32%, model uses normalised 20%
        self.gov_size = 20.0
        self.peak_size = 20.0
        self.baseline = 20.0
        self.debt = 0.0
        self.tariffs = {}

        self.escalation_cooldown = 0
        self.last_tariff_peak = 0.03   # starting from 3% baseline

        # Trade balance (updated each step by the model)
        self.exports = 0.0
        self.imports = 0.0
        self.trade_balance = 0.0

    def initialize_tariffs(self, countries):
        for c in countries:
            if c != self.country:
                self.tariffs[c] = 0.03   # WTO MFN baseline ≈ 3%

    def get_tariff_to(self, target):
        return self.tariffs.get(target, 0.03)

    def _total_lobbying(self):
        return sum(
            org.lobbying_power
            for org in self.model.agents_by_type[Organization]
            if org.country == self.country and not org.bankrupt
        )

    def step(self):
        # ── 1. Bilateral ratchet (step-wise + back-and-forth) ─────────────────
        # Each step ≈ 1 month; escalation rounds happen every ~2-3 months (cooldown=8)
        if self.escalation_cooldown > 0:
            self.escalation_cooldown -= 1

        for other in self.model.agents_by_type[State]:
            if other.country == self.country:
                continue
            their_rate = other.tariffs.get(self.country, 0.03)
            my_rate = self.tariffs.get(other.country, 0.03)

            # Crisis only starts after a 5-step warm-up period
            if self.model.global_crisis and self.model.steps >= 5:
                if self.country in ("USA", "China") and other.country in ("USA", "China"):
                    if my_rate >= 0.30:
                        # Near ceiling: diplomatic pressure → partial back-off
                        # (mirrors Phase 1 deals, temporary truces)
                        if self.random.random() < 0.15:
                            self.tariffs[other.country] = max(
                                0.12, my_rate - self.retaliation_intensity
                            )
                            self.escalation_cooldown = 10
                    elif self.escalation_cooldown == 0:
                        if their_rate > my_rate + 0.005:
                            # Tit-for-tat retaliation
                            self.tariffs[other.country] = min(
                                my_rate + self.retaliation_intensity, 0.35
                            )
                        else:
                            # Autonomous escalation (slower)
                            self.tariffs[other.country] = min(
                                my_rate + self.retaliation_intensity * 0.35, 0.35
                            )
                        self.escalation_cooldown = 8
            else:
                # No crisis: tariffs drift down slowly, held up by lobbying floor
                lobby_floor = 0.03 + self._total_lobbying() * self.lobbying_sensitivity * 0.04
                self.tariffs[other.country] = max(lobby_floor, my_rate * 0.988)

        # ── 2. Government size ratchet (Higgs Effect) ─────────────────────────
        # Each new tariff record triggers a step-wise government expansion.
        # In reality: emergency spending, subsidies, stimulus — locked in permanently.
        max_my_tariff = max(self.tariffs.values()) if self.tariffs else 0.03
        if self.model.global_crisis:
            if max_my_tariff > self.last_tariff_peak + 0.03:
                # Additive jump of +1.5 pp GDP — realistic for trade-war stimulus rounds
                self.gov_size = min(self.gov_size + 1.5, 35.0)
                self.last_tariff_peak = max_my_tariff
            self.peak_size = max(self.peak_size, self.gov_size)
            self.debt += self.gov_size * 0.02
            if self.debt > 3000:
                self.gov_size = max(self.baseline, self.gov_size * 0.997)
        else:
            # Peace: new floor is halfway between old baseline and peak (ratchet)
            self.baseline = 20.0 + (self.peak_size - 20.0) * 0.5
            lobby_floor = self.baseline + self._total_lobbying() * self.lobbying_sensitivity * 0.3
            self.gov_size = max(lobby_floor, self.gov_size * 0.980)


class Organization(mesa.Agent):
    """
    Firm agent with sector heterogeneity and bankruptcy.

    Cost structure calibrated to reality:
      - Fixed overhead (rent, contracted wages, debt service) ≈ 65% of normal revenue
      - Variable costs (materials, energy, logistics) ≈ 25% of production
      - Normal profit margin ≈ 10% of revenue
      - Firms go bankrupt after ~30-40 months of sustained losses
        (cumulative_loss threshold = 15 ≈ ~30 months at -0.5/month loss rate)
    """

    def __init__(
        self,
        model,
        country,
        trade_stickiness=0.40,
        expectation_adaptation_rate=0.15,
        production_elasticity=0.40,
    ):
        super().__init__(model)
        self.country = country
        self.trade_stickiness = trade_stickiness
        self.expectation_adaptation_rate = expectation_adaptation_rate
        self.production_elasticity = production_elasticity

        # Sector assignment
        self.sector = self.random.choice(SECTORS)
        sp = SECTOR_PARAMS[self.sector]
        self.tariff_sensitivity = sp["tariff_sens"]
        self.lobby_efficiency = sp["lobby_eff"]

        # Initialize production to per-firm demand share (no sector overcapacity at start)
        base = model.base_global_demand / (3.0 * model.n_firms_per_country)
        self.production = base * (1.0 + self.random.uniform(-0.10, 0.10))
        self.actual_demand = self.production
        self.expected_demand = self.production
        self.demand_history = [self.production] * 6

        # CEE-SAC parameters
        self.alpha = self.production
        self.beta = 0.0

        # Financials
        # Fixed overhead = 65% of initial revenue — permanent burden regardless of output
        self.initial_production = self.production
        self.fixed_cost = self.production * 0.65
        self.profit = 0.0
        self.cumulative_loss = 0.0
        self.rent = 0.0
        self.lobbying_power = 0.0

        # Investment level
        self.investment = 1.0

        # Bankruptcy flag
        self.bankrupt = False

    # ── private helpers ────────────────────────────────────────────────────────

    def _my_state(self):
        for s in self.model.agents_by_type[State]:
            if s.country == self.country:
                return s
        return None

    def _avg_outgoing_tariff(self):
        s = self._my_state()
        if not s:
            return 0.03
        others = [c for c in self.model.countries if c != self.country]
        base = float(np.mean([s.get_tariff_to(c) for c in others])) if others else 0.03
        return base * self.tariff_sensitivity

    def _avg_incoming_tariff(self):
        others = [c for c in self.model.countries if c != self.country]
        rates = []
        for c in others:
            for s in self.model.agents_by_type[State]:
                if s.country == c:
                    rates.append(s.get_tariff_to(self.country))
        return float(np.mean(rates)) if rates else 0.03

    def _update_expectations(self):
        """CEE-SAC: α (long-run mean) and β (autocorrelation) update."""
        lr = self.expectation_adaptation_rate
        history = np.array(self.demand_history[-10:])
        self.alpha = (1.0 - lr) * self.alpha + lr * float(np.mean(history))
        if len(history) >= 3:
            x_t, x_lag = history[1:], history[:-1]
            var = float(np.var(x_lag))
            if var > 1e-9:
                cov = float(np.mean((x_t - np.mean(x_t)) * (x_lag - np.mean(x_lag))))
                raw_beta = cov / var
                self.beta = (1.0 - lr) * self.beta + lr * raw_beta
                self.beta = float(np.clip(self.beta, -0.95, 0.95))
        last = self.demand_history[-1]
        self.expected_demand = max(0.01, self.alpha + self.beta * (last - self.alpha))

    # ── main step ──────────────────────────────────────────────────────────────

    def step(self):
        if self.bankrupt:
            # Skeleton fixed costs keep bleeding (cannot immediately shed rent/wages)
            self.production = 0.01
            self.profit = -(self.fixed_cost * 0.05)
            self.cumulative_loss += abs(self.profit)
            # Recovery: demand must clearly recover before re-entering market
            if self.expected_demand > self.alpha * 1.08 and self.random.random() < 0.12:
                self.bankrupt = False
                self.cumulative_loss = 0.0
                self.production = self.alpha * 0.45
                self.investment = 0.65
            return

        self._update_expectations()

        # Investment adjusts with expectations (positive beta → invest more)
        inv_target = 1.0 + float(np.clip(self.beta, -0.5, 0.5)) * 0.3
        self.investment = 0.85 * self.investment + 0.15 * inv_target

        # Production target: expectations × tariff friction × investment
        out_tariff = self._avg_outgoing_tariff()
        friction = 1.0 - out_tariff * 0.55
        target = self.expected_demand * friction * self.investment
        adjustment = (target - self.production) * self.production_elasticity
        self.production = max(0.01, self.production + adjustment)

        self.actual_demand = self.model.get_demand_for(self.country)

        # ── Realistic profit = revenue − (fixed overhead + variable costs) ────
        # Revenue: sector value-add pricing + small domestic protection from tariffs
        in_tariff = self._avg_incoming_tariff()
        sp = SECTOR_PARAMS[self.sector]
        price_factor = sp["prod_mult"] * (1.0 + in_tariff * 0.08)
        revenue = self.actual_demand * price_factor

        # Fixed overhead cannot be cut when demand falls (the key bankruptcy driver)
        variable_cost = self.production * 0.25
        self.profit = revenue - (self.fixed_cost + variable_cost)

        # Tariff rent for lobbying (separate from profit)
        self.rent = max(0.0, self.actual_demand * in_tariff * 0.18)

        # Lobbying accumulates with sector-specific efficiency
        self.lobbying_power = min(
            2.0,
            self.lobbying_power * 0.93 + self.rent * 0.05 * self.lobby_efficiency
        )

        # Bankruptcy tracking
        if self.profit < 0:
            self.cumulative_loss += abs(self.profit)
        else:
            self.cumulative_loss = max(0.0, self.cumulative_loss - self.profit * 0.6)

        # Threshold ≈ 15: represents ~30 months of sustained losses before exit
        if self.cumulative_loss > 15.0:
            self.bankrupt = True
            self.production = 0.01

        self.demand_history.append(self.actual_demand)
        if len(self.demand_history) > 20:
            self.demand_history.pop(0)


class Resident(mesa.Agent):
    """
    Consumer agent.
    Calibrated to realistic tariff pass-through rates:
      - Tariff pass-through to consumer prices ≈ 100% (US evidence from 2018-2019)
      - Unemployment from trade wars: modest (2-5% in exposed regions)
      - Welfare loss: ~0.5-1.5% of income per household
    """

    def __init__(self, model, country, price_sensitivity=0.60):
        super().__init__(model)
        self.country = country
        self.price_sensitivity = price_sensitivity   # 60% tariff pass-through to welfare

        self.income = 10.0 + self.random.uniform(-1.0, 1.0)
        self.consumption = self.income * 0.80
        self.domestic_share = 0.60
        self.welfare = self.consumption
        self.savings = self.income * 0.20

    def _avg_import_tariff(self):
        for s in self.model.agents_by_type[State]:
            if s.country == self.country:
                others = [c for c in self.model.countries if c != self.country]
                rates = [s.get_tariff_to(c) for c in others]
                return float(np.mean(rates)) if rates else 0.03
        return 0.03

    def _local_unemployment(self):
        """Unemployment proxy: bankrupt firm share in this country."""
        firms = [o for o in self.model.agents_by_type[Organization] if o.country == self.country]
        if not firms:
            return 0.0
        return sum(1 for o in firms if o.bankrupt) / len(firms)

    def step(self):
        tariff = self._avg_import_tariff()
        unemployment = self._local_unemployment()

        # Tariff raises import prices; unemployment erodes income
        price_index = 1.0 + tariff * self.price_sensitivity
        effective_income = self.income * (1.0 - unemployment * 0.40)

        # Precautionary savings rise with uncertainty
        uncertainty = tariff + unemployment * 0.4
        savings_rate = min(0.45, 0.20 + uncertainty * 0.18)
        self.savings = effective_income * savings_rate

        self.consumption = max(0.10, effective_income * (1.0 - savings_rate) / price_index)
        self.domestic_share = min(0.90, 0.60 + tariff * 0.25)

        # Welfare: consumption minus price burden minus unemployment disutility
        # Real household welfare loss ≈ 0.5-1.5% of income per 10% tariff increase
        self.welfare = (
            self.consumption
            * (1.0 - tariff * 0.12)
            * (1.0 - unemployment * 0.25)
        )
