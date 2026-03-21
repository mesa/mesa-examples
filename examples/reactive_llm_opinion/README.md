# Reactive LLM Opinion Dynamics (Mesa 4.0 Proof of Concept)

## Abstract
This model demonstrates a "Reactive Trigger" architecture for integrating Large Language Models (LLMs) into Agent-Based Models (ABM). Traditional LLM-based agents often suffer from high latency and API costs due to calling reasoning engines at every step. This example showcases how to use Mesa 4.0's batch processing to invoke LLM reasoning only when specific environmental conditions are met, significantly optimizing performance.

## Research Question
Can a "Reactive Trigger" architecture maintain complex social reasoning while reducing LLM API overhead in a large-scale Agent-Based Model?

## Model Description
The model currently implements the core logic for reactive agent updates:
* **Trigger Mechanism:** Agents monitor a "step condition" (simulating an environmental signal or delta threshold).
* **Reactive Logic:** When the condition is met, the model utilizes a batch command to trigger the `process_opinion` method across the agent set.
* **Architecture:** Designed to be lightweight and scalable, avoiding the overhead of individual agent scheduling.

## Technical Implementation (Mesa 4.0 Standards)
This example is built to showcase the **Mesa 4.0 "Clean Slate"** API:
* **AgentSet.do()**: Demonstrates the new standard for batch execution. Instead of a legacy scheduler, the model explicitly triggers agent behaviors.
* **Modern API**: Utilizes the `mesa.Model` and `mesa.Agent` classes in a way that is forward-compatible with the upcoming Mesa 4.0 transition.
* **Separation of Concerns:** Clearly separates standard stepping from conditional high-cognitive (LLM) processing.

## How to Run
1. **Setup Environment**:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1  # Windows
   pip install mesa solara
   ```  <-- (Add these triple backticks here!)

2. **Run the Model**:
   `python model.py`

3. (Planned) Run the visualization:
   `solara run app.py`

## References
* Mesa 4.0 Discussion #2972 (Performance Benchmarking)
* Mesa Examples Guidelines #390