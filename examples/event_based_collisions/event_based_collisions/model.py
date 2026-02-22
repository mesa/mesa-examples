"""
A Mesa model of colliding discs using discrete event scheduling on a continuous
timeline.
"""

import math

import numpy as np
from mesa import Model
from mesa.experimental.continuous_space import ContinuousSpace

from .agents import DiscAgent

PLACEMENT_RADIUS = 25


class DiscModel(Model):
    def __init__(
        self,
        rng: int = 42,
        n_discs: int = 4,
        disc_radius: float = 1.0,
        disc_speed: float = 1.0,
        space_width: int = 100,
        space_height: int = 75,
    ):
        super().__init__(rng=int(rng))
        self.n_discs = n_discs
        self.disc_radius = disc_radius
        # To ensure equal results in simulations with a very high amount of
        # timesteps, disc_speed is NOT used in floating point math, where
        # compounding inaccuracies can cause diverging model states. Instead, we
        # only adjust the time scale when sampling the discs' positions, which
        # is not affected by compounding inaccuracies.
        self.speed_multiplier = disc_speed
        self.space_width = space_width
        self.space_height = space_height

        # Set up the space
        self.space = ContinuousSpace(
            [[0, space_width], [0, space_height]],
            torus=False,
            random=self.random,
            n_agents=n_discs,
        )

        # We use a nested model in our model, which is exclusively responsible
        # for timekeeping and events. This way, we can use custom time scales!
        # Advancing the visualization by 1 time step doesn't have to mean that
        # only 1 time unit has passed. We can now cover 10 time units per time
        # step or only 0.1 time units per time step for example.
        self.time_model = Model()

        # Create the agents
        # -----------------
        # Place the discs in a circle
        disc_positions: list[tuple[float, float]] = [
            (
                (space_width / 2)
                + PLACEMENT_RADIUS * math.cos(2 * math.pi * (i / n_discs)),
                (space_height / 2)
                + PLACEMENT_RADIUS * math.sin(2 * math.pi * (i / n_discs)),
            )
            for i in range(n_discs)
        ]
        # Randomize initial disc trajectory directions
        disc_directions = self.rng.random(size=(self.n_discs,)) * np.array(2 * math.pi)
        DiscAgent.create_agents(
            self,
            self.n_discs,
            self.space,
            self.time_model,
            list(range(n_discs)),
            initial_position=disc_positions,
            initial_direction=disc_directions,
        )
        # Have all agents calculate their next collisions
        for disc in self.agents:
            disc.schedule_next_collisions()

    def step(self):
        normalized_time = self.steps * self.speed_multiplier
        # Resolve all collisions during the time step (only changes trajectories)
        self.time_model.run_until(normalized_time)
        # Have all agents update their position at this point in time, based on
        # their trajectories.
        self.agents.do("update_position", normalized_time)
