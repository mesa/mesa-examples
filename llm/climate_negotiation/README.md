# Climate Negotiation - Mesa-LLM Example

A multi-agent simulation of international climate treaty negotiations where six
country agents, each powered by an LLM negotiate a shared emissions-reduction
target over multiple rounds.

## What This Model Demonstrates

| Mesa-LLM feature | How it appears in this model |
|---|---|
| `STLTMemory` | Short-term memory stores recent proposals and messages; long-term memory consolidates committed positions across rounds |
| `ReActReasoning` | Agents reason about their economic interests and negotiating position, then act |
| `speak_to` (inbuilt tool) | Direct diplomatic messaging between specific countries |
| Custom `@tool` functions | `make_proposal`, `accept_proposal`, `form_coalition`, `reject_and_counter` |
| `vision=-1` | Each agent observes all others and model a  negotiating room with no spatial grid |

## Countries and Their Profiles

Data sources: IEA 2022 (emissions), World Bank 2023 (GDP).

| Country | Emissions (tCO₂/capita) | GDP/capita | Stance |
|---------|------------------------|------------|--------|
| USA | 14.0 | $76,000 | Supports action; insists all major economies especially China and India to match commitments; prefers market-based mechanisms |
| EU | 6.0 | $37,000 | High ambition (Fit for 55, 55% by 2030); pushes legally binding targets and developing-nation finance |
| China | 8.0 | $12,700 | Argues developed nations bear historical responsibility; supports long-term goals contingent on tech transfer and green finance |
| India | 2.0 | $2,500 | Defends common but differentiated responsibilities; energy access for 1.4 billion people is non-negotiable |
| Brazil | 2.8 | $10,400 | Emissions driven by deforestation, not fossil fuels; demands forest conservation credits count in treaty text |
| Russia | 12.5 | $15,000 | Accepts climate science; resists near-term targets that threaten fossil fuel revenues; open to long timelines |

## Negotiation Tools

```
speak_to(listener_ids, message)            - targeted diplomatic message to specific parties
make_proposal(reduction%, year, reason)    - formal proposal broadcast to all
accept_proposal(proposer_id, %, message)   - formal acceptance; marks agent as treaty signatory
form_coalition(partner_ids, name)          - build or expand an alliance
reject_and_counter(proposer_id, %, reason) - reject a proposal and broadcast a counter-offer
```

A **treaty is reached** when at least 2/3 of countries have formally called `accept_proposal`.

## Sample Run Results

**With `openai/gpt-4o` - treaty reached in 6 rounds (~4 minutes)**

```
Round 1  Coalition-building. India forms "Developing Nations Unity" (China, Brazil).
         EU builds a cross-bloc coalition. USA anchors EU + Russia.
Round 2  First proposals. USA: 30% (market mechanisms). EU: 40% by 2040. India: 20%.
Round 3  Counters. India rejects EU 40% -> 20%. EU meets India at 30%.
         China: 20% contingent on tech transfer. Brazil rejects USA -> 25% + forest credits.
Round 4  EU accepts Brazil (25%). Russia accepts China (20%). 2/6 accepted.
Round 5  India accepts Brazil (25%). China updates to 25%. 3/6 accepted.
Round 6  USA accepts EU. Russia upgrades to 25%. TREATY REACHED - 4/6 ≥ 2/3

Final: USA 30%  EU 30%  India 25%  Russia 25% (accepted)
       China 25%   Brazil 25% (pledged but held out for concessions)
```

**With `ollama/llama3.2` (local 3B model)**

The simulation loop runs without errors but smaller local models produce weaker
emergent behaviour: repeated proposals with empty justifications, and attempts to
use non-existent agent IDs. The code guards against both,
but `llama3.2` is best used for testing the simulation loop rather than observing realistic diplomacy. Use `gpt-4o-mini` or `gemini/gemini-2.0-flash` for meaningful negotiations.

## Robustness Against LLM Hallucinations

Two common failure modes are guarded in code:

- **Phantom agent IDs in `form_coalition`** - `partner_ids` are filtered against
  the live agent set before being stored. Invalid IDs are dropped and logged as
  `WARNING` in `climate_negotiation.log`.
- **Invalid `proposer_id` in `accept_proposal`** - the ID is validated before
  recording an acceptance. If it doesn't match any agent, an error string listing
  valid IDs is returned to the LLM so it can self-correct on its next step.

Every agent's step prompt also includes an explicit `VALID COUNTRY IDs` block so
models are less likely to invent IDs in the first place.

## Run Log

Each run writes a structured trace to `climate_negotiation.log` (configurable via
the `CLIMATE_LOG_FILE` environment variable). The log records:

- Round start/end with average pledge, total proposals, and treaty status
- Per-agent state (pledge, accepted, coalition) at the start and end of each round
- Every tool call with its arguments and outcome
- `WARNING` entries for any hallucinated IDs that were dropped

## Setup

### 1. Install dependencies

```bash
pip install mesa-llm mesa solara python-dotenv rich
```

### 2. Set your API key

Create a `.env` file in `llm/climate_negotiation/`:

```
# For Gemini (free tier available)
GEMINI_API_KEY=your_key_here

# OR for OpenAI
OPENAI_API_KEY=your_key_here

# OR for Anthropic
ANTHROPIC_API_KEY=your_key_here

# OR for a local model via Ollama (loop testing only)
OLLAMA_API_BASE=http://localhost:11434
```

### 3. Run with Solara visualisation

```bash
cd llm/climate_negotiation
solara run app.py
```

### 4. Run headless (terminal only)

```bash
cd llm/climate_negotiation
python -m climate_negotiation.model
```

## Supported LLMs

Works with any LiteLLM-compatible model string:

| Model string | Notes |
|---|---|
| `gemini/gemini-2.0-flash` | Default; free tier, fast |
| `openai/gpt-4o` | Best emergent behaviour (tested ✓) |
| `openai/gpt-4o-mini` | Good balance of quality and cost |
| `anthropic/claude-haiku-4-5-20251001` | Capable, low latency |
| `ollama/llama3.2` | Local; suitable for loop testing only |

## File Structure

```
llm/climate_negotiation/          # example root
├── app.py                        # Solara visualisation entry point
├── README.md
└── climate_negotiation/          # Python package
    ├── __init__.py               # triggers tool registration on import
    ├── agents.py                 # CountryAgent, country_tool_manager
    ├── tools.py                  # four custom @tool functions
    └── model.py                  # ClimateNegotiationModel + COUNTRIES configs
```

## Visualisation

The Solara dashboard shows:

- **Pledge bar chart** - each country's current reduction commitment; bars turn green when a country accepts the treaty
- **Coalition status panel** - live table of pledge, acceptance status, coalition members, and proposals made
- **Pledge trajectories** - line chart of all countries' pledges across rounds
- **Time-series plots** - TotalProposals, AveragePledge, LargestCoalitionSize

## What to Watch For

- **Round 1–2**: Coalition-building; agents probe positions before making formal proposals
- **Round 3–4**: Formal proposals emerge; developing nations counter with differentiated targets and conditions
- **Round 5+**: Coalition pressure on holdouts; some countries accept, others counter-propose
- **Treaty achieved**: Green bars in the visualisation, `treaty_reached=True` in the log

## Extending This Example To Try Different Possibilities

**Try different LLMs**: Change `llm_model` in `app.py`. `gpt-4o` produces richer diplomatic
language; `gemini-2.0-flash` is faster and free.

**Add more countries**: Add a new dict to the `COUNTRIES` list in `model.py` and assign it
a system prompt encoding that country's real-world stance.

**Change the treaty threshold**: Edit `_treaty_reached()` in `model.py`
(currently requires a 2/3 majority).

**Use CoTReasoning**: Replace `ReActReasoning` with `CoTReasoning` in `app.py` to see
step-by-step chain-of-thought reasoning printed alongside each agent action.

**Swap memory type**: Replace `STLTMemory` (default) with `EpisodicMemory` for
importance-scored memory retrieval - useful to observe which proposals agents
consider most significant across many rounds.

## Related Work

- Duffuant, G. & Weisbuch, G. (2002). *Bounded confidence and social networks.*
  - The `deffuant_weisbuch` example shows opinion convergence without LLM reasoning.
  Compare its convergence speed with this model's negotiated consensus.
