# LLM Prisoner's Dilemma

## Summary

An iterated Prisoner's Dilemma simulation where agents use **LLM Chain-of-Thought reasoning** to decide whether to cooperate or defect each round — instead of following fixed strategies like tit-for-tat or always-defect.

## The Game

Each round, agents are randomly paired. Both must simultaneously choose:

- **cooperate** 🤝 — work together for mutual benefit
- **defect** 🗡️ — betray partner for personal gain

**Payoff matrix:**

|  | Partner Cooperates | Partner Defects |
|--|-------------------|-----------------|
| **You Cooperate** | 3, 3 | 0, 5 |
| **You Defect** | 5, 0 | 1, 1 |

## What makes this different from classical models

Classical Prisoner's Dilemma ABM uses fixed strategies — always defect, always cooperate, tit-for-tat, random. The outcome is determined by the strategy rules.

Here, agents **reason** at each step:

> "My partner cooperated last round. That signals trustworthiness.
> If I defect now I gain 5 points but destroy the trust we've built.
> Over many rounds, mutual cooperation (3+3+3...) beats cycles of
> defection (1+1+1...). I'll cooperate."

This produces **emergent negotiation dynamics** — reputation building, trust signaling, strategic exploitation — that fixed rules cannot capture.

## Visualization

- **Cooperation rate plot** — fraction of cooperative actions per round
- **Cumulative plot** — total cooperations vs defections over time

**Initial state (Step 0):**

![Initial state — no history, agents have not yet played](prisoners_dilemma_initial.png)

**After 5 rounds of LLM-driven reasoning:**

![5 rounds — cooperation collapses after exploitation, mutual defection locks in](prisoners_dilemma_dashboard.png)

**What this run demonstrates — emergent game theory from pure LLM reasoning:**

| Round | Cooperation Rate | What happened |
|-------|-----------------|---------------|
| 1 | 0.5 | One agent tried cooperation to build trust; the other defected and exploited it |
| 2 | 0.5 | Cooperating agent gave a second chance, exploiter defected again |
| 3+ | 0.0 | Exploited agent switched to permanent defection — "I cooperated twice, got burned twice, I'm done" |
| 4–5 | 0.0 | Stable mutual defection — the Nash equilibrium lock-in |

**Why this matters:** This is the core result from Axelrod's *Evolution of Cooperation* (1984) — agents that try cooperation, get exploited, and retaliate with defection — reproduced here with **zero hardcoded strategy**. No tit-for-tat rule, no punishment parameter, no threshold. The LLM reasoned its way to this behavior by reflecting on its interaction history at each step.

This is something a fixed-strategy model simply cannot do: the agent articulates *why* it switched, references past betrayal in its reasoning chain, and makes a strategic decision grounded in language rather than math.

## How to Run

```bash
cp .env.example .env  # fill in your API key
pip install -r requirements.txt
solara run app.py
```

## Supported LLM Providers

Gemini, OpenAI, Anthropic, Ollama (local) — configured via `.env`.

## Reference

Axelrod, R. (1984). *The Evolution of Cooperation*. Basic Books.
