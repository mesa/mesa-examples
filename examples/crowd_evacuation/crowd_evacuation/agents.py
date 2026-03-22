"""Person agent for the Crowd Evacuation model.

Implements a simplified Social Force Model (Helbing & Molnár, 1995).
"""

import numpy as np
from mesa.experimental.continuous_space import ContinuousSpaceAgent


class Person(ContinuousSpaceAgent):
    def __init__(
        self,
        space,
        model,
        position=(0, 0),
        desired_speed=1.3,
        max_speed=2.0,
    ):
        super().__init__(space, model)
        self.position = position
        self.velocity = np.zeros(2)
        self.desired_speed = desired_speed  # comfortable walking speed (m/s)
        self.max_speed = max_speed
        self.radius = 0.25  # roughly half a shoulder width
        self.mass = 80.0  # kg, used for F=ma
        self.escaped = False

        self._social_strength = 80.0  # agent-agent repulsion strength (N)
        self._social_range = 0.6  # repulsion falloff distance (m)
        self._wall_strength = 120.0  # wall repulsion strength (N)
        self._wall_range = 0.4  # wall repulsion falloff (m)
        self._relax_time = 0.3  # how fast agent adjusts to desired velocity (s)



    def _nearest_exit(self):
        """Return (direction_unit_vector, distance) toward the closest exit."""
        pos = np.asarray(self.position, dtype=float)
        best_dir = np.zeros(2)
        best_dist = float("inf")

        for exit_center, _width in self.model.exits:
            diff = np.asarray(exit_center, dtype=float) - pos
            d = np.linalg.norm(diff)
            if d < best_dist:
                best_dist = d
                best_dir = diff / d if d > 0 else diff

        return best_dir, best_dist

    def _desired_force(self):
        """Pull toward the exit at the agent's preferred speed."""
        direction, _ = self._nearest_exit()
        desired_vel = direction * self.desired_speed
        return self.mass * (desired_vel - self.velocity) / self._relax_time

    def _social_force(self):
        """Repulsion from nearby people — nobody likes being squished."""
        force = np.zeros(2)
        neighbors, distances = self.get_neighbors_in_radius(radius=3.0)
        if not neighbors:
            return force

        pos = np.asarray(self.position, dtype=float)

        for other, dist in zip(neighbors, distances):
            if other is self:
                continue

            if dist < 1e-6:
                angle = self.model.random.uniform(0, 2 * np.pi)
                force += (
                    np.array([np.cos(angle), np.sin(angle)]) * self._social_strength
                )
                continue

            away = (pos - np.asarray(other.position, dtype=float)) / dist
            gap = dist - (self.radius + other.radius)

            repulsion = self._social_strength * np.exp(
                -max(gap, 0) / self._social_range
            )
            force += repulsion * away

            if gap < 0:
                force += 500.0 * abs(gap) * away

        return force

    def _wall_force(self):
        """Repulsion from room boundaries — don't walk through walls.

        The tricky part: we need to SKIP repulsion for the section of wall
        where an exit is, otherwise agents can never leave the room.
        """
        force = np.zeros(2)
        pos = np.asarray(self.position, dtype=float)
        w, h = self.model.width, self.model.height

        walls = [
            (pos[0], np.array([1.0, 0.0]), "left"),
            (w - pos[0], np.array([-1.0, 0.0]), "right"),
            (pos[1], np.array([0.0, 1.0]), "bottom"),
            (h - pos[1], np.array([0.0, -1.0]), "top"),
        ]

        for dist_to_wall, normal, wall_id in walls:
            if self._at_exit_opening(pos, wall_id):
                continue

            gap = dist_to_wall - self.radius
            if gap < 2.0:
                repulsion = self._wall_strength * np.exp(
                    -max(gap, 0) / self._wall_range
                )
                force += repulsion * normal

                if gap < 0:
                    force += 800.0 * abs(gap) * normal

        return force

    def _at_exit_opening(self, pos, wall_id):
        """Check if we're at the opening of an exit on this specific wall.

        Only suppresses wall force for the specific wall that has an exit,
        and only when the agent is lined up with the gap.
        """
        for exit_center, exit_w in self.model.exits:
            ec = np.asarray(exit_center, dtype=float)

            exit_wall = None
            if ec[0] <= 0.01:
                exit_wall = "left"
            elif ec[0] >= self.model.width - 0.01:
                exit_wall = "right"
            elif ec[1] <= 0.01:
                exit_wall = "bottom"
            elif ec[1] >= self.model.height - 0.01:
                exit_wall = "top"

            if exit_wall != wall_id:
                continue
            if wall_id in ("left", "right"):
                if abs(pos[1] - ec[1]) < exit_w * 2.0:
                    return True
            else:
                if abs(pos[0] - ec[0]) < exit_w * 2.0:
                    return True

        return False

    def _reached_exit(self):
        """Has this agent made it to an exit?

        Uses a generous detection zone: within 2x exit_width of the center.
        This prevents agents getting stuck at the boundary edge.
        """
        pos = np.asarray(self.position, dtype=float)
        for exit_center, exit_w in self.model.exits:
            ec = np.asarray(exit_center, dtype=float)
            if np.linalg.norm(pos - ec) < exit_w * 1.5:
                return True
        return False

    def step(self):
        """One tick of the simulation: compute forces → move → check exit."""
        if self.escaped:
            return

        dt = self.model.dt

        total_force = self._desired_force() + self._social_force() + self._wall_force()

        self.velocity += (total_force / self.mass) * dt

        speed = np.linalg.norm(self.velocity)
        if speed > self.max_speed:
            self.velocity *= self.max_speed / speed

        new_pos = np.asarray(self.position, dtype=float) + self.velocity * dt

        margin = 0.05
        new_pos[0] = np.clip(new_pos[0], margin, self.model.width - margin)
        new_pos[1] = np.clip(new_pos[1], margin, self.model.height - margin)
        self.position = new_pos

        # 4. CHECK IF WE MADE IT OUT
        if self._reached_exit():
            self.escaped = True
            self.model.agents_escaped += 1
