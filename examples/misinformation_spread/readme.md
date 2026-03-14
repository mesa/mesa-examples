## Misinformation Spread Model (LLM vs Rule-Based)

A Mesa agent-based model simulating how misinformation spreads across a
social network when agents reason using an LLM versus fixed probability
rules. Models how different personality types (believers, skeptics, and
spreaders) produce group dynamics that no individual agent
was programmed to exhibit.

## Overview

Agents are placed on an Erdos-Renyi graph and exposed to a misinformation
claim. Each step, agents decide whether to believe and share the claim
based on their personality type and how many times they have
previously encountered it. LLM agents accumulate a decision history
across steps, allowing social pressure to build up over time.

The key behavior is the S-curve effect: LLM-driven skeptics
initially resist the claim for several steps, but repeated exposure
gradually tips them toward belief. This pattern that emerges purely from
prompt context and not hard-coded thresholds.

## Installation
```bash
git clone <your-repo-url>
cd misinformation_spread
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**LLM requirement:** This model uses [Ollama](https://ollama.com) for
local LLM inference. Install Ollama and pull the model before running:
```bash
ollama pull llama3
```

## Running the Model

**Static comparison (2-panel chart):**
```bash
python run.py
```

**Interactive dashboard:**
```bash
solara run app.py
```

## Parameters

- **n_believers** (default: 4) - number of believer agents. Tend to trust
  and share information easily; belief strengthens with repeated exposure
- **n_skeptics** (default: 3) — number of skeptic agents. Initially
  resistant; may gradually convince after many exposures
- **n_spreaders** (default: 2) — number of spreader agents. Share
  everything to maximize engagement regardless of truth
- **connectivity** (default: 0.3) — probability of a connection between
  any two agents in the Erdos-Renyi graph. Higher values produce denser
  networks with faster spread
- **misinformation_claim** (default: cold water digestion claim) — the
  claim being spread. Can be replaced with any string
- **rng** (default: 42) — random seed for reproducibility

## Model Details

**Agents:**

- `BelieverAgent` — LLM agent that trusts information easily. Passes
  times_exposed and full decision history into the prompt each step,
  allowing accumulated exposure to strengthen belief over time.
- `SkepticAgent` — LLM agent that questions claims. Starts resistant but
  the accumulation mechanism means repeated exposures gradually
  reduce skepticism, producing delayed belief.
- `SpreaderAgent` — LLM agent that shares everything to maximize
  engagement. Almost always says yes, reinforced by seeing the claim
  spread further each step.
- `RuleBasedBeliever`, `RuleBasedSkeptic`, `RuleBasedSpreader` — identical
  network structure but fixed probability thresholds (80%, 15%, 95%).
  Used as a baseline to isolate the effect of LLM reasoning.

**Architecture note:**

`ReActReasoning.plan()` wraps all output in `reasoning:` / `action:`
fields regardless of prompt instructions, making structured two-line
responses unparsable. This model bypasses `ReActReasoning` entirely and
calls `litellm.completion()` directly, which produces clean
`BELIEVE: yes / SHARE: yes` output that can be reliably parsed.

**Network:**

Built using `networkx.erdos_renyi_graph` and wrapped in Mesa's `Network`
discrete space. Misinformation is seeded by broadcasting from all
spreaders to all agents at initialization. Each step, any agent with
`shared=True` propagates the claim to all other agents.

**Social pressure mechanism:**

Each agent tracks `times_exposed` and a `history` list of past decisions.
Both are passed into the LLM prompt each step so the model can reason
about change over time rather than making independent per-step decisions.

## Output

**run.py produces 2 panels:**
- Spread count over time for LLM vs rule-based agents
- Final convinced count by agent type (believers, skeptics, spreaders)

**app.py produces an interactive dashboard with:**
- Spread Over Time: live line chart comparing LLM vs rule-based S-curves
- Final Counts: bar chart of convinced agents by type at end of run
- Raw Data: step-by-step dataframes for both models

## Project Structure
```
misinformation_spread/
├── agents.py           # LLM agent classes (Believer, Skeptic, Spreader)
├── model.py            # MisinformationModel and RuleBasedMisinformationModel
├── rulebased_agents.py # Rule-based agent classes for baseline comparison
├── run.py              # Run both models and generate static comparison chart
├── app.py              # Interactive Solara dashboard
├── readme.md           # This file
├── requirements.txt
├── tests/
│   └── test_model.py   # pytest suite (rule-based only, no LLM calls)
└── images/             # Output charts saved here
```

## References

- Vosoughi, S. et al. (2018). The spread of true and false news online.
  *Science.*
