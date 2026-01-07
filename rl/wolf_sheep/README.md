# Collaborative Survival: Wolf-Sheep Predation Model

This project demonstrates the use of the RLlib library to implement Multi-Agent Reinforcement Learning (MARL) in the classic Wolf-Sheep predation problem. The environment details can be found on the Mesa project's GitHub repository [here](https://github.com/mesa/mesa-examples/tree/main/examples/wolf_sheep).

## Key Features

**RLlib and Multi-Agent Learning**:
- **Library Utilized**: The project leverages the RLlib library to concurrently train two independent PPO (Proximal Policy Optimization) agents.
- **Agents**:
  - **Wolf**: Predatory agent survives by eating sheep
  - **Sheep**: Prey agent survives by eating grass
  - **Grass**: Grass is eaten by sheep and regrows with time

**Input and Observation Space**:
- **Observation Grid**: Each agent's policy receives a 10x10 grid centered on itself as input.
  - **Grid Details**: The grid incorporates information about the presence of other agents (wolves, sheep, and grass) within the grid.
  - **Agent's Energy Level**: The agent's current energy level is also included in the observations.

**Action Space**:
- **Action Space**: The action space is the ID of the neighboring tile to which the agent wants to move.

**Behavior and Training Outcomes**:
- **Optimal Behavior**:
  - **Wolf**: Learns to move towards the nearest sheep.
  - **Sheep**: Learns to run away from wolves and is attracted to grass.
- **Density Variations**: You can vary the densities of sheep and wolves to observe different results.

By leveraging RLlib and Multi-Agent Learning, this project provides insights into the dynamics of predator-prey relationships and optimal behavior strategies in a simulated environment.


<p align="center">
<img src="resources/wolf_sheep.gif" width="500" height="400">
</p>