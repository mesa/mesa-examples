# Climate Negotiation - Mesa-LLM Example

A multi-agent simulation of international climate treaty negotiations where six
country agents — each powered by an LLM — negotiate a shared emissions-reduction
target over multiple rounds.

## What This Model Demonstrates

| Mesa-LLM feature | How it appears in this model |
|---|---|
| `STLTMemory` | Short-term memory stores recent proposals and messages; long-term memory consolidates committed positions across rounds |
| `ReActReasoning` | Agents reason about their economic interests and negotiating position, then act |
| `speak_to` (inbuilt tool) | Direct diplomatic messaging between specific countries |
| Custom `@tool` functions | `make_proposal`, `accept_proposal`, `form_coalition`, `reject_and_counter` |
| `vision=-1` | Each agent observes all others — modelling a plenary negotiating room with no spatial grid |

## Countries and Their Profiles

| Country | Emissions (tCO₂/capita) | GDP/capita | Stance |
|---------|------------------------|------------|--------|
| USA | 14.5 | $65,000 | Supports action; insists developing nations match commitments |
| EU | 6.4 | $35,000 | High ambition; pushes binding targets and developing-nation finance |
| China | 7.1 | $12,000 | Argues for differentiated responsibility; needs tech transfer |
| India | 1.9 | $2,200 | Energy access first; very low historical per-capita emissions |
| Brazil | 2.2 | $8,600 | Forest conservation must count; wants ecosystem payment |
| Russia | 11.4 | $12,000 | Gradual transition; fossil fuel dependent |

## Negotiation Tools

```
speak_to(listener_ids, message)            - diplomatic message to specific parties
make_proposal(reduction%, year, reason)   - formal proposal broadcast to all
accept_proposal(proposer_id, %, message)  - formal acceptance of a proposal
form_coalition(partner_ids, name)         - build an alliance
reject_and_counter(proposer_id, %, reason)- reject + counter-propose
```

A **treaty is reached** when at least 2/3 of countries have formally accepted
a common proposal.

## Setup

### 1. Install dependencies

```bash
pip install mesa-llm mesa solara python-dotenv rich
```

### 2. Set your API key

Create a `.env` file in `examples/climate_negotiation/`:

```
# For Gemini (free tier available)
GEMINI_API_KEY=your_key_here

# OR for OpenAI
OPENAI_API_KEY=your_key_here

# OR for a local model via Ollama
OLLAMA_API_BASE=http://localhost:11434
```

### 3. Run with Solara visualization

```bash
cd examples/climate_negotiation
solara run app.py
```

### 4. Run headless (terminal only)

```bash
cd examples/climate_negotiation
python -m climate_negotiation.model
```

## File Structure

```
climate_negotiation/          //example root
├── app.py                    //Solara visualization entry point
├── README.md
└── climate_negotiation/      //Python package
    ├── __init__.py           //triggers tool registration on import
    ├── agents.py             //CountryAgent, country_tool_manager
    ├── tools.py              //four custom @tool functions
    └── model.py              //ClimateNegotiationModel + country configs
```

## What to Watch For

- **Round 1–2**: Agents send diplomatic messages, probe positions, and form initial coalitions
- **Round 3–4**: Formal proposals emerge; developing nations counter with differentiated targets
- **Round 5+**: Coalitions pressure outliers; some countries accept, others counter-propose
- **Treaty achieved**: Green bars in the visualization indicate accepted countries

## Extending This Example

**Try different LLMs**: Change `llm_model` in `app.py`. Gemini 2.0 Flash is fast and free;
GPT-4o produces richer diplomatic language.

**Add more countries**: Add a new dict to the `COUNTRIES` list in `model.py`.

**Change the treaty threshold**: Edit `_treaty_reached()` in `model.py`
(currently requires 2/3 majority).

**Use CoTReasoning instead**: Replace `ReActReasoning` with `CoTReasoning` in `app.py`
to see step-by-step chain-of-thought reasoning in agent decisions.

**Swap memory type**: Replace `STLTMemory` (the default) with `EpisodicMemory` for
importance-scored memory retrieval — useful to see which proposals agents
consider most significant.

## Related Work

- Duffuant, G. & Weisbuch, G. (2002). *Bounded confidence and social networks.*
  — The `deffuant_weisbuch` example shows opinion dynamics without LLM reasoning.
  Compare its convergence behaviour with this model's LLM-driven negotiation.
- Park, J. S. et al. (2023). *Generative Agents: Interactive Simulacra of Human Behavior.*
  — Inspired the EpisodicMemory system used in Mesa-LLM.
