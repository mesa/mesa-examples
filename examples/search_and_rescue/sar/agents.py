"""Base agents for the search and rescue model.

Responders sweep a disaster area looking for victims. They carry no group
state of their own: which crew a responder belongs to, and which pool it is
on call for, is held entirely by the membership backend and queried through
``model.meta_agents``.
"""

from __future__ import annotations

import numpy as np
from mesa.experimental.continuous_space import ContinuousSpaceAgent

GENERALIST = "generalist"
MEDIC = "medic"


class Victim(ContinuousSpaceAgent):
    """A casualty waiting to be found and reached.

    A victim that is not reached before ``expires_at`` is lost, which is what
    makes the response policy matter.
    """

    def __init__(self, space, model, position, severity, deadline, critical_severity):
        """Place a victim and start its survival clock."""
        super().__init__(space, model)
        self.position = np.asarray(position, dtype=float)
        self.severity = float(severity)
        self.needs_medic = self.severity >= critical_severity
        self.expires_at = model.time + deadline
        self.discovered = False
        self.found_at = None
        self.assigned_crew = None

    @property
    def is_expired(self) -> bool:
        """Whether this victim's survival window has closed."""
        return self.model.time >= self.expires_at


class Responder(ContinuousSpaceAgent):
    """A searcher. Either a generalist or a medic.

    Medics are the scarce resource: only a medic can complete a rescue of a
    critical victim, and every medic is simultaneously a member of its home
    crew and on call to the medical pool.
    """

    def __init__(self, space, model, position, specialty, speed):
        """Place a responder in the space."""
        super().__init__(space, model)
        self.position = np.asarray(position, dtype=float)
        self.specialty = specialty
        self.speed = float(speed)

    @property
    def is_medic(self) -> bool:
        """Whether this responder can complete a critical rescue."""
        return self.specialty == MEDIC

    def search(self, radius: float) -> list[Victim]:
        """Discover any undiscovered victims within ``radius``."""
        neighbors, _ = self.get_neighbors_in_radius(radius)
        found = []
        for neighbor in neighbors:
            if isinstance(neighbor, Victim) and not neighbor.discovered:
                neighbor.discovered = True
                neighbor.found_at = self.model.time
                found.append(neighbor)
        return found

    def move_towards(self, target_position: np.ndarray) -> None:
        """Step at most ``speed`` units toward a point."""
        delta = np.asarray(target_position, dtype=float) - self.position
        distance = float(np.linalg.norm(delta))
        if distance <= self.speed or distance == 0.0:
            self.position = self._clamp(np.asarray(target_position, dtype=float))
        else:
            self.position = self._clamp(self.position + delta / distance * self.speed)

    def wander(self) -> None:
        """Take a random step while no victim is assigned."""
        angle = self.model.random.uniform(0, 2 * np.pi)
        step = np.array([np.cos(angle), np.sin(angle)]) * self.speed
        self.position = self._clamp(self.position + step)

    def _clamp(self, position: np.ndarray) -> np.ndarray:
        """Keep a position inside the (non-toroidal) space bounds."""
        bounds = self.space.dimensions
        return np.clip(position, bounds[:, 0], bounds[:, 1])
