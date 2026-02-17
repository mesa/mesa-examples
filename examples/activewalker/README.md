# Active Walker Model

## Summary

The Active Walker Model simulates human pedestrians navigating across a grassy landscape between multiple destination points. As walkers repeatedly traverse the same routes, they wear down the grass, creating visible paths that emerge from the collective behavior of individuals making independent decisions. This creates an emergent system where paths self-organize through the physical interaction of walkers with their environment.

In the model, agents (human walkers):
- Start at random positions with designated destinationskv
- Move based on three competing forces:
  - **Destination pull**: attraction toward their target location
  - **Path following**: preference to walk on already worn areas (lower grass density)
  - **Inertia**: resistance to sudden direction changes
- Wear down grass as they walk, creating visible trails
- Reach their destination and receive a new one, creating cyclical behavior

As the simulation runs, walkers collectively create increasingly well-defined pathways connecting the destination points, demonstrating how simple individual navigation decisions can produce sophisticated collective path systems without any explicit coordination. These emergent routes often converge to efficient solutions, mirroring observed patterns in real-world human trail formation on university campuses, parks, and other open spaces.

## Model Behavior

The visualization shows three key elements:

1. **Agent Positions** (left): Red dots represent pedestrians navigating the landscape
2. **Path Heatmap** (bottom right): Heatmap showing which paths are most frequently taken by the agents, with hotter colors indicating heavily traversed routes
3. **Grass Density Gradient** (top right): Heatmap showing the distribution of worn areas that walkers use for navigation

The images below demonstrate the evolution of grass wear patterns over time as walkers develop increasingly defined pathways:

### Early Stage (Step 188)
<table><tr>
<td><img width="576" height="408" alt="Early Stage - Step 188" src="https://github.com/user-attachments/assets/92c3fe7d-49f8-482d-aac3-528b199912ae" /></td>
<td><img width="703" height="438" alt="Mid Stage - Step 714" src="https://github.com/user-attachments/assets/62cb1ecc-c50c-48e1-8925-1a30e4c54333" /></td>
</tr></table>

### Later Stages
<table><tr>
<td><img width="706" height="406" alt="Later Stage - Step 1449" src="https://github.com/user-attachments/assets/a2cb0f11-1883-4f80-9a54-c4e080cec903" /></td>
<td><img width="599" height="413" alt="Advanced Stage - Step 6219" src="https://github.com/user-attachments/assets/7b329a29-0ac7-4765-9d30-9b78873b65d0" /></td>
</tr></table>


## Installation

To install the dependencies, use `pip` to install `mesa`:

```bash
    $ pip install mesa
```

## How to Run

To run the model interactively with the Solara visualization, run `solara run` in this directory:

```bash
    $ solara run app.py
```

Then open your browser to [http://localhost:8765/](http://localhost:8765/) and press Reset, then Run.

You can adjust the following parameters in real-time:
- **Number**: Population size of pedestrians
- **speed**: Pedestrian movement speed
- **min trail strength**: Minimum grass wear value
- **max trail strength**: Maximum grass wear value
- **agent print strength**: How much grass wear each pedestrian creates with each step
- **trail dies in**: Steps until grass recovers (wears back to original state)
- **vision**: Radius for sensing worn path gradients
- **resolution of trail grid**: Grid resolution for grass wear tracking

## Files

* **`model.py`**
* **`agent.py`**
* **`app.py`**

## Further Reading

This model is inspired by and related to:

**Primary Reference:**
- **Helbing, D., Schweitzer, F., Keltsch, J., & Molnar, P. (1997).** "Active Walker Model for the Formation of Human and Animal Trail Systems." *Physical Review Letters*, 81(15), 3287. https://arxiv.org/abs/cond-mat/9806097
  - Seminal work demonstrating how individual movement decisions lead to collective path formation through repeated interactions with the environment.

