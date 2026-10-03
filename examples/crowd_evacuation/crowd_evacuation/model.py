"""Crowd Evacuation Model.
Simulates people evacuating a room through exits using the
Social Force Model (Helbing & Molnár, 1995). Built on Mesa's ContinuousSpace.
"""

import numpy as np
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.experimental.continuous_space import ContinuousSpace

from .agents import Person


class EvacuationModel(Model):
    def __init__(
        self,
        num_people=80,
        width=30,
        height=20,
        num_exits=2,
        exit_width=1.5,
        desired_speed=1.3,
        max_speed=2.0,
        rng=None,
    ):
        super().__init__(rng=rng)

        self.width = width
        self.height = height
        self.num_people = num_people
        self.dt = 0.1  # each step = 0.1 seconds of simulated time
        self.agents_escaped = 0

        self.exits = self._place_exits(num_exits, exit_width)

        self.space = ContinuousSpace(
            [[0, width], [0, height]],
            torus=False,
            random=self.random,
            n_agents=num_people,
        )

        margin = 1.0
        for _ in range(num_people):
            x = self.random.uniform(margin, width - margin)
            y = self.random.uniform(margin, height - margin)
            Person(
                space=self.space,
                model=self,
                position=(x, y),
                desired_speed=desired_speed,
                max_speed=max_speed,
            )

        self.datacollector = DataCollector(
            model_reporters={
                "Agents Remaining": lambda m: m.num_people - m.agents_escaped,
                "Agents Escaped": lambda m: m.agents_escaped,
                "Average Speed": self._avg_speed,
            },
        )
        self.datacollector.collect(self)

    def _place_exits(self, num_exits, exit_width):
        """Put exits on the walls — opposite walls for better flow.

        Returns list of (center_position, width) tuples.
        """
        exits = []

        if num_exits >= 1:
            # Right wall, centered vertically
            exits.append((np.array([self.width, self.height / 2]), exit_width))
        if num_exits >= 2:
            # Left wall
            exits.append((np.array([0.0, self.height / 2]), exit_width))
        if num_exits >= 3:
            # Top wall
            exits.append((np.array([self.width / 2, self.height]), exit_width))
        if num_exits >= 4:
            # Bottom wall
            exits.append((np.array([self.width / 2, 0.0]), exit_width))

        return exits

    def _avg_speed(self):
        """Average speed of people still in the room."""
        active = [a for a in self.agents if not a.escaped]
        if not active:
            return 0.0
        return float(np.mean([np.linalg.norm(a.velocity) for a in active]))

    def step(self):
        """One tick: move everyone, collect data, check if done."""
        active = [a for a in self.agents if not a.escaped]
        self.random.shuffle(active)
        for agent in active:
            agent.step()

        self.datacollector.collect(self)

        # All out? We're done.
        if self.agents_escaped >= self.num_people:
            self.running = False
