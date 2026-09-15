# Misinformation Spread Model

## Summary

An agent-based model simulating the spread of misinformation through a small community, built with mesa-llm. LLM-powered agents with unique personas (teacher, shopkeeper, journalist, doctor, etc.) reason about whether to spread or challenge a rumor about water contamination. Includes a rule-based comparison model to demonstrate the difference between LLM-driven and traditional agent behavior.

This model demonstrates mesa-llm features including: ReAct reasoning, custom tools, inter-agent communication, and memory.

## How to Run

### LLM Version (requires Ollama)

1. Install Ollama from https://ollama.com
2. Pull a model: `ollama pull llama3.2:3b`
3. Run: `python run.py`

### Rule-Based Version (no LLM needed)

```
python run_comparison.py
```

## Files

- `misinformation_spread/model.py`: MisinformationModel (LLM) and RuleBasedModel (rule-based) classes
- `misinformation_spread/agents.py`: CitizenAgent (LLM-powered) and RuleBasedAgent classes
- `misinformation_spread/tools.py`: Custom tools for agent actions (check_neighbors, spread_rumor, challenge_rumor, update_belief)
- `run.py`: Runs the LLM simulation for 5 steps with 12 agents and plots results
- `run_comparison.py`: Runs the rule-based simulation for 10 steps and plots results

## Key Findings

- Small local LLMs (3B parameters) struggle with multi-step tool calling in mesa-llm's ReAct loop
- Built-in mesa-llm tools can confuse agents — removing unnecessary ones improves behavior
- Rule-based model runs instantly vs 25+ minutes for LLM version with local inference
- LLM agents show personality-driven reasoning but need larger models for reliable tool use

## Further Reading

- [Mesa-LLM documentation](https://mesa-llm.readthedocs.io)
- [Mesa framework](https://mesa.readthedocs.io)
- [Generative Agents paper](https://arxiv.org/abs/2304.03442)
