# Tariff War: Ratchet Effects & Trade Diversion

An agent-based model (ABM) of a bilateral trade war between two major economies (USA and China) and a neutral third party (Neutral Asia), built with [Mesa 3](https://github.com/projectmesa/mesa).

## Overview

This model simulates the cascading economic consequences of an escalating trade war, demonstrating six key macroeconomic phenomena that emerge from micro-level agent interactions:

1. **Higgs Ratchet Effect** — Government size expands step-wise during each escalation round and never fully contracts, permanently raising the fiscal baseline.
2. **Trade Diversion** — Neutral Asia captures a bounded share of the bilateral trade USA and China lose to each other, yielding a short-term GDP boost.
3. **Self-fulfilling Recession Spiral (CEE-SAC)** — Firms update demand expectations using sample autocorrelation (β). Once β turns negative, falling expectations reduce investment and production, which further reduces actual demand — a self-reinforcing contraction.
4. **Endogenous Interests Ratchet** — Tariff rents are converted into lobbying power, which raises the political floor for tariff reduction even after the crisis ends.
5. **Resource Misallocation** — Rising tariffs distort global production, shrinking the total economic pie via a country-specific efficiency multiplier.
6. **Firm Bankruptcy & Unemployment** — Sustained losses from fixed overhead exceeding revenue drive firm exits, which then reduce consumer income and welfare.

## Calibration

Parameters are grounded in the 2018–2025 US–China trade war:

| Parameter | Value | Basis |
|-----------|-------|-------|
| Baseline tariff | 3% | WTO MFN average |
| Peak tariff cap | 35% | 2018–19 peak ~25%; 2025 exceeded 100% on some goods |
| Retaliation per round | 8% | ~10% per escalation round historically |
| Escalation cooldown | 8 steps | ~2–3 months between rounds |
| Government size baseline | 20% of GDP | USA ~21%, China ~32% |
| Government size cap | 35% of GDP | Wartime upper bound |
| Firm fixed cost ratio | 65% of revenue | Rent, contracted wages, debt service |
| Variable cost ratio | 25% of production | Materials, energy, logistics |
| Normal profit margin | ~10% | Competitive manufacturing/tech |
| Bankruptcy threshold | ~30 months of losses | Historical firm exit timelines |

## Model Structure

### Agents

**`State`** — Nation-state (3 instances: USA, China, Neutral Asia)
- Implements bilateral tariff ratchet with cooldown-based escalation
- Diplomatic back-off at ceiling (15% chance), creating realistic back-and-forth
- Government size ratchet: +1.5 pp GDP per new tariff record, never fully returns
- Lobbying floor prevents tariffs from falling back to baseline post-crisis

**`Organization`** — Firm (default: 6 per country × 3 countries = 18 total)
- Three sectors: **Tech** (high tariff sensitivity, premium pricing), **Agriculture** (commodity pricing, hit hardest by retaliation), **Manufacturing** (baseline)
- CEE-SAC expectation formation: α (long-run mean) + β (autocorrelation trend)
- Fixed overhead + variable cost structure — demand drops tip firms into losses
- Cumulative loss bankruptcy with probabilistic market-recovery restart

**`Resident`** — Consumer (default: 8 per country × 3 = 24 total)
- Tariff-driven price index reduces real consumption
- Unemployment proxy from local bankruptcy rate erodes income
- Precautionary savings rise with uncertainty
- Welfare composite: consumption × price burden × employment

### Key Mechanisms

```
Tariff escalation (State)
    ↓
Demand shock (Model.get_demand_for)        ← country-specific efficiency
    ↓
Falling revenue < Fixed costs (Organization)
    ↓
Negative profit → Cumulative loss → Bankruptcy
    ↓
Higher unemployment (Resident)
    ↓
Lower consumption → Lower cross-border demand
    ↓
Further demand drop (self-fulfilling spiral)
```

## Visualization

Seven real-time charts rendered with Solara + Matplotlib:

| Chart | What to look for |
|-------|-----------------|
| **Firm Pessimism (β) & Lobbying** | β crossing zero into negative territory signals the recession spiral onset |
| **Expected vs Actual Production** | Widening gap reveals forecast error accumulation |
| **Bilateral Tariffs** | Staircase pattern = ratchet; dips = diplomatic back-off |
| **Government Size** | Step-wise jumps that never return to baseline |
| **Country GDP & Trade Balance** | Neutral Asia GDP rising while USA/China fall |
| **Firm Health** | Bankruptcy rate rising 20–40 steps after crisis begins; sector divergence |
| **Consumer Welfare** | Neutral Asia residents fare better; USA/China households bear the cost |

## Installation & Running

```bash
pip install -r requirements.txt
solara run app.py
```

Then open [http://localhost:8765](http://localhost:8765) in your browser.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| Trigger Tariff Shock | `True` | Enable the trade war crisis |
| Base Global Demand | 100 | Total demand units in the world economy |
| Retaliation Intensity | 0.08 | Tariff increase per escalation round (8%) |
| Lobbying Sensitivity | 0.25 | How strongly lobbying raises the tariff floor |
| Expectation Adaptation Rate | 0.15 | Speed of CEE-SAC β updating |
| Production Elasticity | 0.40 | How fast firms adjust output to expectations |
| Trade Stickiness | 0.40 | Inertia in trade relationship switching |
| Firms per Country | 6 | Number of firm agents per country |

**Note:** After adjusting sliders, click **Reset** to restart the simulation with the new parameters.

## Theoretical Background

- **Higgs (1987)** — *Crisis and Leviathan*: government grows during emergencies and retains the new size.
- **CEE-SAC (Evans & Honkapohja, 2001)** — Consistent Expectations Equilibrium with sample autocorrelation learning: agents estimate β from historical demand, creating self-fulfilling boom/bust cycles.
- **Trade Diversion (Viner, 1950)** — When two large trading partners restrict bilateral trade, third-party suppliers capture diverted orders.
- **Endogenous Interests (Grossman & Helpman, 1994)** — Industries convert tariff rents into political contributions that perpetuate protection.

## File Structure

```
tarrif_war/
├── app.py                  # Solara visualization (7 charts + parameter panel)
├── requirements.txt
├── readme.md
└── tarrif_war/
    ├── __init__.py
    ├── agent.py            # State, Organization, Resident agents
    └── model.py            # TariffWarModel, demand formula, trade flows
```
