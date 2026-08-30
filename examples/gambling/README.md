# Luck vs Skill in Short-Term Gambling

This example demonstrates how short-term gambling success is dominated by luck,
even when agents differ in skill.

## Model Description

Each agent has a fixed skill level between 0 and 1. Skill slightly increases the
probability of winning a bet, but outcomes are still stochastic.

Agents repeatedly place fixed-size bets. After a short number of rounds, agents
are ranked by wealth.

The model compares the average skill of:
- The top 10% of agents by wealth
- The bottom 10% of agents by wealth

## Key Insight

Over short horizons, the skill distributions of winners and losers differ only slightly.
Early success is therefore a poor indicator of true skill.

This illustrates why gambling success, early trading profits, or beginner's luck
are often misattributed to ability rather than chance.

This model demonstrates:
1. Beginner’s luck is a real statistical phenomenon
2. Early winners are not reliable indicators of skill
3. Skill emerges only over long horizons
4. Human inference from short samples is systematically biased

## How to Run

```bash
solara run app.py
