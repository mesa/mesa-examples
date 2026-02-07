"""
A colliding disc Mesa agent using Mesa's DEVSimulator.
"""

from __future__ import annotations

import math
from enum import Enum
from typing import Any

import numpy as np
from mesa.experimental.continuous_space import ContinuousSpaceAgent

# A disc always has a speed of 1.0! If the model is mandating a different disc
# speed, it instead uses a different time scale to simulate the same effect.
# This is done to avoid compounding inaccuracies in floating point math across
# models with different disc speed settings.
DISC_SPEED = 1.0


class Border(Enum):
    RIGHT = 1
    TOP = 2
    LEFT = 3
    BOTTOM = 4


class DiscAgent(ContinuousSpaceAgent):
    def __init__(
        self,
        model,
        space,
        devs_model,
        id,
        initial_position,
        initial_direction,
    ):
        super().__init__(space, model)
        self.id = id
        self.devs_model = devs_model
        self.position = initial_position
        self.trajectory_init_pos = initial_position
        self.trajectory_init_pos_time = float(self.model.steps)
        self.trajectory_direction = initial_direction
        self.trajectory_id = 0
        """The trajectory id is changed every time the trajectory changes and
        hence allows the detection of collision events that are no longer valid."""

    def position_at_time(self, time: float) -> tuple[float, float]:
        """Determine the disc's position at the given time with it's current trajectory.

        Doesn't consider collisions, only the current trajectory!"""
        time_since_trajectory_init_pos = time - self.trajectory_init_pos_time
        x_pos = self.trajectory_init_pos[0] + (
            DISC_SPEED
            * time_since_trajectory_init_pos
            * math.cos(self.trajectory_direction)
        )
        y_pos = self.trajectory_init_pos[1] + (
            DISC_SPEED
            * time_since_trajectory_init_pos
            * math.sin(self.trajectory_direction)
        )
        return (x_pos, y_pos)

    def earliest_border_collision(
        self, exempt_border: Border | None = None
    ) -> dict[str, Any]:
        """Determine the next border the disc will collide with.

        Parameters
        ----------
        exempt_border: Border | None
            Ignore collisions with this given border. If you're resolving a collision
            with a border right now, provide this argument to avoid another immediate
            collision with it. Default: None

        Returns
        -------
        dict
            This dict is to be used as parameters by the discrete event simulator when
            it calls `resolve_border_collision`.
        """
        x_speed = DISC_SPEED * math.cos(self.trajectory_direction)
        y_speed = DISC_SPEED * math.sin(self.trajectory_direction)

        # Determine earliest border collision
        min_border_collision_time = float("inf")
        border_collision_kwargs = None
        if exempt_border != Border.RIGHT and x_speed > 0:
            collision_time = self.trajectory_init_pos_time + (
                (
                    self.model.space_width
                    - self.model.disc_radius
                    - self.trajectory_init_pos[0]
                )
                / x_speed
            )
            if collision_time < min_border_collision_time:
                min_border_collision_time = collision_time
                border_collision_kwargs = {
                    "trajectory_id": self.trajectory_id,
                    "border": Border.RIGHT,
                    "collision_loc": self.position_at_time(collision_time),
                    "collision_time": collision_time,
                }
        if exempt_border != Border.LEFT and x_speed < 0:
            collision_time = self.trajectory_init_pos_time + (
                (self.trajectory_init_pos[0] - self.model.disc_radius) / -x_speed
            )
            if collision_time < min_border_collision_time:
                min_border_collision_time = collision_time
                border_collision_kwargs = {
                    "trajectory_id": self.trajectory_id,
                    "border": Border.LEFT,
                    "collision_loc": self.position_at_time(collision_time),
                    "collision_time": collision_time,
                }
        if exempt_border != Border.TOP and y_speed > 0:
            collision_time = self.trajectory_init_pos_time + (
                (
                    self.model.space_height
                    - self.model.disc_radius
                    - self.trajectory_init_pos[1]
                )
                / y_speed
            )
            if collision_time < min_border_collision_time:
                min_border_collision_time = collision_time
                border_collision_kwargs = {
                    "trajectory_id": self.trajectory_id,
                    "border": Border.TOP,
                    "collision_loc": self.position_at_time(collision_time),
                    "collision_time": collision_time,
                }
        if exempt_border != Border.BOTTOM and y_speed < 0:
            collision_time = self.trajectory_init_pos_time + (
                (self.trajectory_init_pos[1] - self.model.disc_radius) / -y_speed
            )
            if collision_time < min_border_collision_time:
                min_border_collision_time = collision_time
                border_collision_kwargs = {
                    "trajectory_id": self.trajectory_id,
                    "border": Border.BOTTOM,
                    "collision_loc": self.position_at_time(collision_time),
                    "collision_time": collision_time,
                }
        assert border_collision_kwargs is not None
        return border_collision_kwargs

    def disc_collision_time(self, other: DiscAgent) -> float | None:
        """Determine if self and the other disc will collide, and if they do, when?

        (Only considering the trajectories they have right now, disregarding other
        collisions.)
        """
        self_x_speed = DISC_SPEED * math.cos(self.trajectory_direction)
        self_y_speed = DISC_SPEED * math.sin(self.trajectory_direction)
        other_x_speed = DISC_SPEED * math.cos(other.trajectory_direction)
        other_y_speed = DISC_SPEED * math.sin(other.trajectory_direction)
        rel_x_speed = self_x_speed - other_x_speed
        rel_y_speed = self_y_speed - other_y_speed

        initial_time = max(
            self.trajectory_init_pos_time, other.trajectory_init_pos_time
        )
        self_pos = self.position_at_time(initial_time)
        other_pos = other.position_at_time(initial_time)
        rel_x_pos = self_pos[0] - other_pos[0]
        rel_y_pos = self_pos[1] - other_pos[1]
        radius = self.model.disc_radius

        # Need to solve for time:
        # (rel_x_pos + rel_x_speed * time)**2
        # + (rel_y_pos + rel_y_speed * time)**2
        # = (2 * radius)**2

        # Solving with quadratic formula; the equation a * time**2 + b * time + c = 0
        # is solved with:
        # time = (-b +/- sqrt(b**2 - 4*a*c)) / (2*a)

        a = rel_x_speed**2 + rel_y_speed**2
        b = 2 * (rel_x_pos * rel_x_speed + rel_y_pos * rel_y_speed)
        c = (rel_x_pos**2 + rel_y_pos**2) - (2 * radius) ** 2

        # We can't divide by a if a=0. But a=0 means that the relative velocity is zero,
        # therefore no collision if not already touching.
        if math.isclose(a, 0):
            return None

        # The discriminant is the content of the square root (sqrt).
        # If it's negative, there is no solution, so no collision
        discriminant = b**2 - 4 * a * c
        if discriminant < 0:
            return None

        # The quadratic formula calculates two timestamps:
        # One is when the discs start touching and one is when they stop touching
        # (if they would move through each other without colliding).
        # We only care about when they start touching, which is earlier in time.
        rel_collision_time_1 = (-b + math.sqrt(discriminant)) / (2 * a)
        rel_collision_time_2 = (-b - math.sqrt(discriminant)) / (2 * a)
        rel_collision_time = min(rel_collision_time_1, rel_collision_time_2)

        # No collisions before the trajectory started
        if rel_collision_time < 0:
            return None
        abs_collision_time = initial_time + rel_collision_time
        # No collisions earlier than the simulator's current time
        if abs_collision_time < self.devs_model.time:
            return None
        return abs_collision_time

    def update_position(self, normalized_time):
        # All collisions have to be resolved at this point already.
        # Just update your current position at this time based on your trajectory.
        self.position = np.array(self.position_at_time(normalized_time))

    def schedule_next_collisions(
        self,
        exempt_border: Border | None = None,
        exempt_disc: DiscAgent | None = None,
    ):
        # Schedule border collision
        border_collision_kwargs = self.earliest_border_collision(exempt_border)
        self.model.devs.schedule_event_absolute(
            function=self.resolve_border_collision,
            time=border_collision_kwargs["collision_time"],
            function_kwargs=border_collision_kwargs,
        )

        # Schedule disc collisions
        for disc in self.model.agents:
            if disc is self or disc is exempt_disc:
                continue
            collision_time = self.disc_collision_time(disc)
            if collision_time is not None:
                self.model.devs.schedule_event_absolute(
                    function=self.resolve_disc_collision,
                    time=collision_time,
                    function_kwargs={
                        "own_trajectory_id": self.trajectory_id,
                        "own_collision_loc": self.position_at_time(collision_time),
                        "other_disc": disc,
                        "other_trajectory_id": disc.trajectory_id,
                        "other_collision_loc": disc.position_at_time(collision_time),
                        "collision_time": collision_time,
                    },
                )

    def resolve_border_collision(
        self, trajectory_id: int, border: Border, collision_loc, collision_time
    ):
        if self.trajectory_id != trajectory_id:
            # The trajectory has changed; this collision doesn't happen after all
            return
        if border == Border.RIGHT:
            normal_angle = 1.0 * math.pi
        elif border == Border.TOP:
            normal_angle = 1.5 * math.pi
        elif border == Border.LEFT:
            normal_angle = 0.0 * math.pi
        else:  # border == Border.BOTTOM:
            normal_angle = 0.5 * math.pi
        self.trajectory_init_pos = collision_loc
        self.trajectory_init_pos_time = collision_time
        self.trajectory_direction = reflection_angle(
            self.trajectory_direction, normal_angle
        )
        self.trajectory_id += 1
        self.schedule_next_collisions(exempt_border=border)

    def resolve_disc_collision(
        self,
        own_trajectory_id: int,
        own_collision_loc,
        other_disc,
        other_trajectory_id: int,
        other_collision_loc,
        collision_time,
    ):
        if (
            self.trajectory_id != own_trajectory_id
            or other_disc.trajectory_id != other_trajectory_id
        ):
            # The trajectory has changed; this collision doesn't happen after all
            return
        own_normal_angle = angle_towards(other_collision_loc, own_collision_loc)
        self.trajectory_init_pos = own_collision_loc
        self.trajectory_init_pos_time = collision_time
        self.trajectory_direction = reflection_angle(
            self.trajectory_direction, own_normal_angle
        )
        self.trajectory_id += 1

        other_normal_angle = angle_towards(own_collision_loc, other_collision_loc)
        other_disc.trajectory_init_pos = other_collision_loc
        other_disc.trajectory_init_pos_time = collision_time
        other_disc.trajectory_direction = reflection_angle(
            other_disc.trajectory_direction, other_normal_angle
        )
        other_disc.trajectory_id += 1

        self.schedule_next_collisions(exempt_disc=other_disc)
        other_disc.schedule_next_collisions(exempt_disc=self)


def reflection_angle(incoming_angle: float, normal_angle: float) -> float:
    return (2 * normal_angle - incoming_angle - math.pi) % (2 * math.pi)


def angle_towards(
    start_pos: tuple[float, float], target_pos: tuple[float, float]
) -> float:
    """Calculate the angle that points from start_pos to target_pos"""
    rel_x = target_pos[0] - start_pos[0]
    rel_y = target_pos[1] - start_pos[1]
    return math.atan2(rel_y, rel_x) % (2 * math.pi)
