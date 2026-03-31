"""
Needs-Based Wolf-Sheep Predation Model
========================================

Extends Mesa's core Wolf-Sheep model with needs-based behavioral architecture.
Animals have continuous internal states (hunger, fear, fatigue) that evolve
each step and drive behavior through priority-based decision-making.

Built as a behavioral framework evaluation for GSoC 2026, exploring how well
Mesa supports established behavioral theories. This model evaluates the
needs-based approach specifically, documenting friction points and comparing
emergent dynamics against the core rule-based Wolf-Sheep.

References:
- Mesa core Wolf-Sheep: mesa.examples.advanced.wolf_sheep
- Discussion #2529: Continuous States
- Discussion #2526: Tasks with duration
- Discussion #2538: Behavioral Framework
- Wilensky, U. (1997). NetLogo Wolf Sheep Predation model.
"""

import math

from mesa import Model
from mesa.datacollection import DataCollector
from mesa.discrete_space import OrthogonalVonNeumannGrid
from mesa.experimental.devs import ABMSimulator

from agents import NeedsGrass, NeedsSheep, NeedsWolf


class NeedsWolfSheep(Model):
    """Wolf-Sheep model with needs-based behavioral architecture.

    Key differences from core Wolf-Sheep:
    - Animals have continuous internal states: hunger, fear, fatigue
    - Behavior is driven by which need is most pressing
    - More data collected: average needs levels, action distributions
    """

    description = (
        "Wolf-Sheep Predation with needs-based behavioral architecture. "
        "Animals balance hunger, fear, and fatigue to select actions."
    )

    def __init__(
        self,
        width=20,
        height=20,
        initial_sheep=100,
        initial_wolves=25,
        sheep_reproduce=0.04,
        wolf_reproduce=0.05,
        wolf_gain_from_food=20.0,
        sheep_gain_from_food=4.0,
        grass_regrowth_time=30,
        seed=None,
        simulator: ABMSimulator = None,
    ):
        super().__init__(seed=seed)
        self.simulator = simulator
        self.simulator.setup(self)

        self.width = width
        self.height = height

        # Create grid
        self.grid = OrthogonalVonNeumannGrid(
            [self.height, self.width],
            torus=True,
            capacity=math.inf,
            random=self.random,
        )

        # Data collection — includes needs-based metrics
        # FRICTION: DataCollector works well for model-level aggregates,
        # but collecting per-agent needs over time requires agent_reporters
        # which creates large dataframes. There's no built-in way to
        # efficiently track "average hunger of living wolves" without
        # a custom lambda that handles the empty-agentset case.
        self.datacollector = DataCollector(
            model_reporters={
                "Wolves": lambda m: len(m.agents_by_type[NeedsWolf]),
                "Sheep": lambda m: len(m.agents_by_type[NeedsSheep]),
                "Grass": lambda m: len(
                    m.agents_by_type[NeedsGrass].select(lambda a: a.fully_grown)
                ),
                "Avg Wolf Hunger": lambda m: (
                    m.agents_by_type[NeedsWolf].agg(
                        "hunger", func=lambda x: sum(x) / len(x)
                    )
                    if len(m.agents_by_type[NeedsWolf]) > 0
                    else 0
                ),
                "Avg Sheep Fear": lambda m: (
                    m.agents_by_type[NeedsSheep].agg(
                        "fear", func=lambda x: sum(x) / len(x)
                    )
                    if len(m.agents_by_type[NeedsSheep]) > 0
                    else 0
                ),
            },
            agent_reporters={
                "energy": "energy",
                "hunger": "hunger",
                "fear": "fear",
                "fatigue": "fatigue",
                "last_action": "last_action",
            },
        )

        # Create sheep
        NeedsSheep.create_agents(
            self,
            initial_sheep,
            energy=self.rng.random((initial_sheep,)) * 2 * sheep_gain_from_food,
            p_reproduce=sheep_reproduce,
            energy_from_food=sheep_gain_from_food,
            cell=self.random.choices(self.grid.all_cells.cells, k=initial_sheep),
        )

        # Create wolves
        NeedsWolf.create_agents(
            self,
            initial_wolves,
            energy=self.rng.random((initial_wolves,)) * 2 * wolf_gain_from_food,
            p_reproduce=wolf_reproduce,
            energy_from_food=wolf_gain_from_food,
            cell=self.random.choices(self.grid.all_cells.cells, k=initial_wolves),
        )

        # Create grass patches
        for cell in self.grid:
            fully_grown = self.random.choice([True, False])
            countdown = (
                0 if fully_grown else self.random.randrange(0, grass_regrowth_time)
            )
            NeedsGrass(self, countdown, grass_regrowth_time, cell)

        self.running = True
        self.datacollector.collect(self)

    def step(self):
        """Execute one step: sheep act, then wolves act."""
        # FRICTION: Activation order matters for predator-prey dynamics.
        # Mesa's shuffle_do is clean for this, but there's no built-in
        # way to say "activate sheep and wolves simultaneously" (which
        # would be needed for a PettingZoo Parallel wrapper). The
        # sequential activation (sheep first, then wolves) creates a
        # slight advantage for sheep — they can flee before wolves hunt.
        self.agents_by_type[NeedsSheep].shuffle_do("step")
        self.agents_by_type[NeedsWolf].shuffle_do("step")

        self.datacollector.collect(self)

        # Stop if one species is extinct
        if (
            len(self.agents_by_type[NeedsWolf]) == 0
            or len(self.agents_by_type[NeedsSheep]) == 0
        ):
            self.running = False
