# Active Walker Model

## Summary

The Active Walker Model simulates agents navigating between multiple destination points while leaving pheromone trails that influence their own movement and the movement of other agents. This creates an emergent system where agents collectively develop efficient pathways through repeated interactions with shared chemical signals.

In the model, agents:
- Start at random positions with designated destinations
- Move based on three competing forces:
  - **Destination pull**: attraction toward their target location
  - **Trail following**: attraction to pheromone trails left by other agents
  - **Inertia**: resistance to sudden direction changes
- Leave pheromone trails that decay over time
- Reach their destination and receive a new one, creating cyclical behavior

As the simulation runs, agents in motion create increasingly well-defined pathways connecting the destination points, demonstrating how simple local interactions can produce sophisticated collective navigation patterns. These emergent routes often converge to efficient solutions, similar to ant colony foraging behavior.

## Model Behavior

The visualization shows three key elements:

1. **Agent Positions** (left): Red dots represent active agents navigating the space
2. **Pheromone Trail** (bottom right): Shows the chemical trails left by agents, with intensity indicating strength
3. **Trail Intensity/Gradient** (top right): Heatmap showing the diffused pheromone field that agents use for navigation

The images below demonstrate the evolution of pheromone trails over time as agents develop increasingly defined pathways:

### Early Stage (Step 188)
![Trail at step 188](activewalker_step_188.png)

### Mid Stage (Step 714)
![Trail at step 714](activewalker_step_714.png)

### Later Stage (Step 1449)
![Trail at step 1449](activewalker_step_1449.png)

### Advanced Stage (Step 6219)
![Trail at step 6219](activewalker_step_6219.png)

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
- **Number**: Population size of agents (10-200)
- **speed**: Agent movement speed (0.1-2.0)
- **min trail strength**: Minimum pheromone value (0-1.0)
- **max trail strength**: Maximum pheromone value (1-50)
- **agent print strength**: How much pheromone each agent deposits (1-50)
- **trail dies in**: Steps until pheromone fully decays (100-2001)
- **vision**: Radius for sensing pheromone gradients (2-10)
- **resolution of trail grid**: Grid resolution for pheromone layer (1-10)

## Files

* **`model.py`**: Contains the `activeModel` class that manages the simulation, agent creation, and the `stepDeposit` class for pheromone layer management including diffusion, decay, and deposition mechanics.
* **`agent.py`**: Contains the `activewalker` agent class with movement physics and the `Stop_agent` class for destination locations.
* **`app.py`**: Contains the Solara visualization code with interactive components for viewing agent positions, pheromone trails, and pheromone gradients.

## Further Reading

This model is inspired by:

- **Ant Colony Foraging**: Real ants use pheromone trails for collective navigation. See research on stigmergy (indirect communication through environmental modification).
- **Active Matter Physics**: Self-propelled particles that respond to local chemical cues are studied extensively in physics and active matter literature.
- **Swarm Intelligence**: Collective behavior emerging from simple local interactions without central control.

Related models and concepts:
- Ant Colony Optimization (ACO) algorithms
- Reaction-diffusion systems
- Stigmergy and collective intelligence
