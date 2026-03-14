# LLM Schelling Segregation

An LLM-powered implementation of Schelling's (1971) classic segregation model,
built with [Mesa](https://github.com/projectmesa/mesa) and
[Mesa-LLM](https://github.com/projectmesa/mesa-llm).

## Overview

The Schelling segregation model is one of the most influential agent-based
models ever published. It demonstrates that even mild individual preferences
for same-group neighbors produce strong global segregation — a striking example
of emergent behavior from simple rules.

**Classical model:** An agent moves if fewer than a fixed threshold (e.g. 30%)
of its neighbors share its group.

**This model:** Agents reason in natural language about their neighborhood
composition and decide whether they feel comfortable staying or want to move.
The LLM can weigh contextual factors, producing richer dynamics than a fixed
threshold allows.

## The Model

Agents of two groups (A and B) are placed on a grid. Each step:
1. Each agent observes its Moore neighborhood (up to 8 neighbors)
2. It describes the neighborhood composition in natural language to the LLM
3. The LLM decides: `happy` (stay) or `unhappy` (move)
4. Unhappy agents relocate to a random empty cell

The simulation tracks happiness levels and a segregation index over time.

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `width` | Grid width | 10 |
| `height` | Grid height | 10 |
| `density` | Fraction of cells occupied | 0.8 |
| `minority_fraction` | Fraction of agents in Group B | 0.4 |
| `llm_model` | LLM model string | `gemini/gemini-2.0-flash` |

## Running the Model

Set your API key:
```bash
export GEMINI_API_KEY=your_key_here
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Run the visualization:
```bash
solara run app.py
```

## Comparison with Classical Schelling

| Feature | Classical Schelling | LLM Schelling |
|---------|--------------------|--------------------|
| Decision rule | Fixed threshold (e.g. 30%) | LLM natural language reasoning |
| Agent memory | None | Short-term memory of interactions |
| Flexibility | Rigid | Emergent from reasoning |
| Interpretability | Mathematical | Natural language explanations |

## Reference

Schelling, T.C. (1971). Dynamic models of segregation.
*Journal of Mathematical Sociology*, 1(2), 143–186.
