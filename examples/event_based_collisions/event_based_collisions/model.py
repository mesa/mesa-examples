"""
A Mesa model of colliding discs using Mesa's DEVSimulator.
"""

import math

import numpy as np
from mesa import Model
from mesa.experimental.continuous_space import ContinuousSpace
from mesa.experimental.devs import DEVSimulator

from .agents import DiscAgent

PLACEMENT_RADIUS = 25


class DiscModel(Model):
    def __init__(
        self,
        seed=42,
        n_discs=4,
        disc_radius=1.0,
        disc_speed=1.0,
        space_width=100,
        space_height=75,
    ):
        super().__init__(seed=seed)
        self.n_discs = n_discs
        self.disc_radius = disc_radius
        self.disc_speed = disc_speed
        self.space_width = space_width
        self.space_height = space_height

        # Set up the space
        self.space = ContinuousSpace(
            [[0, space_width], [0, space_height]],
            torus=False,
            random=self.random,
            n_agents=n_discs,
        )

        # Set up discrete event simulator
        self.devs = DEVSimulator()
        # We link the simulator to a dummy model. Linking it to our actual model
        # would change the behavior of the time steps and make visualization
        # harder.
        self.devs.setup(Model())

        # Create the agents
        # -----------------
        # Place the discs in a circle
        disc_positions = [
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
            list(range(n_discs)),
            initial_position=disc_positions,
            initial_direction=disc_directions,
        )
        # Have all agents calculate their next collisions
        for disc in self.agents:
            disc.schedule_next_collisions()

    def step(self):
        # Resolve all collisions during the time step (only changes trajectories)
        self.devs.run_until(self.steps)
        # Have all agents update their position at this point in time, based on
        # their trajectories.
        self.agents.do("update_position")
