# Rumor Mill Model

A simple agent-based simulation showing how rumors spread through a population, implemented with the Mesa framework.

## About

This is an introductory Mesa example that demonstrates:
- Creating agents with simple behaviors
- Using grid-based space (Von Neumann and Moore neighborhoods)
- Collecting and visualizing data
- Building an interactive web interface with SolaraViz

The model is adapted from the NetLogo Rumor Mill model by Uri Wilensky (1999).

**Key Enhancement**: This implementation adds a `rumor_spread_chance` parameter that controls the probability of successful rumor transmission. This allows exploring how transmission uncertainty affects rumor spread dynamics, compared to the deterministic spreading in the original NetLogo model.

## How It Works

Agents are placed on a grid. Some agents start knowing a rumor (red), others don't (blue).

Each simulation step:
1. All per-step counters are reset
2. Each agent who knows the rumor tells one random neighbor
3. The neighbor hears the rumor (counter increments)
4. The neighbor learns the rumor with probability `rumor_spread_chance`
5. Data is collected tracking spread metrics

Key distinction: Agents can **hear** the rumor multiple times, but only **learn** it once (when they first successfully receive it based on the spread chance)

## Installation

```bash
pip install mesa[rec]
```

## Running the Model

Launch the interactive visualization:

```bash
solara run app.py
```


This opens a web interface where you can:
- Adjust parameters with sliders
- Watch the rumor spread in real-time
- View plots of spread metrics

## Parameters

- **know_rumor_ratio** (0.0-1.0): Initial percentage of agents who know the rumor
- **rumor_spread_chance** (0.0-1.0): Probability of successful rumor transmission
- **eight_neighborhood** (True/False): Use 8 neighbors (Moore) vs 4 neighbors (Von Neumann)
- **width/height**: Grid dimensions

## Code Structure

**agent.py** - Defines the Person agent
- `knows_rumor`: Whether agent knows the rumor
- `times_heard`: Total cumulative times agent has heard the rumor
- `times_heard_this_step`: Times agent heard the rumor in current step
- `newly_learned`: Flag for agents who just learned the rumor (never heard before)
- `step()`: Tell a random neighbor if you know the rumor

**model.py** - Defines the RumorMillModel
- Creates grid and agents
- Runs the simulation steps
- Collects three metrics:
  - `Percentage_Knowing_Rumor`: Percentage of all agents who know the rumor
  - `Times_Heard_Rumor_Per_Step`: Total times rumor was heard this step (whether learned or not)
  - `New_People_Knowing_Rumor`: Percentage of new learners this step (people who never heard it before)

**app.py** - Visualization interface
- Grid display with color-coded agents (red = knows, blue = doesn't know)
- Interactive parameter controls
- Real-time charts tracking rumor spread and new learners

## Running Programmatically

```python
from model import RumorMillModel

model = RumorMillModel(
    width=10,
    height=10,
    know_rumor_ratio=0.3,
    rumor_spread_chance=0.5,
    eight_neightborhood=False
)

for i in range(100):
    model.step()

data = model.datacollector.get_model_vars_dataframe()
print(data)
```
## Extensions

This model has been extended with three additions that make rumor dynamics
more realistic and interesting to explore.

### Skepticism
Each agent has a `skepticism` attribute sampled from a normal distribution
around `skepticism_mean`. A skeptical agent is harder to convince — the
effective spread chance is reduced by `rumor_spread_chance * (1 - skepticism)`.
At skepticism 0.5 the rumor struggles to spread at all. At 0.9 it dies out
almost immediately regardless of spread chance.

### Forgetting Mechanic
Agents who know the rumor can forget it each step with probability
`forget_chance`. This prevents the rumor from monotonically saturating
the population. At forget_chance 0.1 with high spread, the rumor reaches
a dynamic equilibrium — new people learn it every step while others forget
it, producing persistent fluctuation rather than a flat ceiling.

### Debunker Agent
A new `Debunker` subclass that actively tells neighbors the rumor is false.
Each step a debunker picks a random neighbor — if that neighbor knows the
rumor, there is a chance they forget it. At 10% debunkers with 10% forget
chance, the rumor never fully saturates and debunker effectiveness fluctuates
between 30-80%, showing an ongoing battle between spreaders and debunkers.

### Key Findings
Setting forget_chance=0.0, skepticism_mean=0.0, fraction_debunkers=0.0
reproduces the original model exactly.

The most interesting dynamics appear when forget_chance and fraction_debunkers
are both set above 0.05 — the rumor reaches a fluctuating equilibrium instead
of saturating, with Percentage_Forgotten and Debunker_Effectiveness both
showing active values throughout the run.

High skepticism (above 0.5) suppresses rumor spread almost entirely even
with high spread chance, suggesting that population-level skepticism is a
stronger brake on rumor dynamics than individual debunking.

## New Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| skepticism_mean | 0.0 | Mean skepticism level across population |
| forget_chance | 0.0 | Probability of forgetting rumor each step |
| fraction_debunkers | 0.0 | Fraction of population that actively debunks |

## New Metrics

| Metric | Description |
|--------|-------------|
| Percentage_Forgotten | Fraction who forgot the rumor this step |
| Debunker_Effectiveness | Success rate of debunkers per step |

## Credits
- The following code was adapted from the Rumor Mill model included in Netlogo:

    https://www.netlogoweb.org/launch#https://www.netlogoweb.org/assets/modelslib/Sample%20Models/Social%20Science/Rumor%20Mill.nlogox
    Wilensky, U. (1999). NetLogo. http://ccl.northwestern.edu/netlogo/.
    Center for Connected Learning and Computer-Based Modeling, Northwestern University, Evanston, IL.
- Mesa framework: https://github.com/projectmesa/mesa
