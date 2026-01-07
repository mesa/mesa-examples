"""
Mesa implementation of Virus/Antibody model: Agents module.
"""

import copy
import weakref
from collections import deque

import numpy as np
from mesa.experimental.continuous_space import ContinuousSpaceAgent


class CellularAgent(ContinuousSpaceAgent):
    def _random_move(self, speed=1):
        """Random walk in a 2D space."""
        perturb = np.array(
            [
                self.random.uniform(-0.5, 0.5),
                self.random.uniform(-0.5, 0.5),
            ]
        )
        self.direction = self.direction + perturb
        norm = np.linalg.norm(self.direction)
        if norm > 0:
            self.direction /= norm
        self.position += self.direction * speed


class AntibodyAgent(CellularAgent):
    """An Antibody agent. They move randomly until they see a virus, go fight it.
    If they lose, stay KO for a bit, lose health and back to random moving.
    """

    speed = 1.5
    sight_range = 10
    ko_timeout = 15
    memory_capacity = 3
    health = 2

    def __init__(
        self,
        model,
        space,
        duplication_rate,
        initial_position=(0, 0),
        direction=(1, 1),
    ):
        super().__init__(model=model, space=space)

        # Movement & characteristics
        self.position = initial_position
        self.direction = np.array(direction, dtype=float)
        self.duplication_rate = duplication_rate

        # Memory
        self.st_memory: deque = deque(maxlen=self.memory_capacity)
        self.lt_memory: list = []

        # Target & KO state
        self.target = None  # will hold a weakref.ref or None
        self.ko_steps_left = 0

    def step(self):
        nearby_agents, _ = self.space.get_agents_in_radius(
            self.position, self.sight_range
        )
        nearby_viruses = [a for a in nearby_agents if isinstance(a, VirusAgent)]
        nearby_antibodies = [
            a
            for a in nearby_agents
            if isinstance(a, AntibodyAgent) and a.unique_id != self.unique_id
        ]

        # Acquire a virus target if we don't already have one
        if self.target is None and nearby_viruses:
            closest = nearby_viruses[0]
            self.target = weakref.ref(closest)

        # Communicate and maybe duplicate
        self.communicate(nearby_antibodies)
        if self.random.random() < self.duplication_rate:
            self.duplicate()

        # Then move
        self.move()

    def communicate(self, nearby_antibodies) -> bool:
        for other in nearby_antibodies:
            to_share = [
                dna for dna in self.st_memory if dna and dna not in other.lt_memory
            ]
            if to_share:
                other.st_memory.extend(to_share)
                other.lt_memory.extend(to_share)
        return True

    def duplicate(self):
        clone = AntibodyAgent(
            self.model,
            self.space,
            duplication_rate=self.duplication_rate,
            initial_position=self.position,
            direction=self.direction,
        )
        # Copy over memory
        clone.st_memory = deque(maxlen=self.memory_capacity)
        clone.st_memory.extend([item for item in self.st_memory if item])
        clone.lt_memory = [item for item in self.lt_memory if item]
        clone.target = None
        clone.ko_steps_left = 0

    def move(self):
        # Dereference weakref if needed
        target = (
            self.target()
            if isinstance(self.target, weakref.ReferenceType)
            else self.target
        )

        new_pos = None

        # KO state: target refers back to self
        if target is self:
            self.ko_steps_left -= 1
            if self.ko_steps_left <= 0:
                self.target = None

        # Random walk if no target
        elif target is None:
            self._random_move()

        # Chase a valid virus target
        else:
            if getattr(target, "space", None) is not None:
                vec = np.array(target.position) - np.array(self.position)
                dist = np.linalg.norm(vec)
                if dist > self.speed:
                    self.direction = vec / dist
                    new_pos = self.position + self.direction * self.speed
                else:
                    self.engage_virus(target)
            else:
                self.target = None

        if new_pos is not None:
            self.position = new_pos

    def engage_virus(self, virus) -> str:
        dna = copy.deepcopy(virus.dna)
        if dna in self.st_memory or dna in self.lt_memory:
            virus.remove()
            self.target = None

        else:
            # KO (or death)
            self.health -= 1
            if self.health <= 0:
                self.remove()

            self.st_memory.append(dna)
            self.lt_memory.append(dna)
            self.ko_steps_left = self.ko_timeout
            # mark KO state by weak-ref back to self
            self.target = weakref.ref(self)
            return "ko"


class VirusAgent(CellularAgent):
    """A virus agent: random movement, mutation, duplication, passive to antibodies."""

    speed = 1

    def __init__(
        self,
        model,
        space,
        mutation_rate,
        duplication_rate,
        position=(0, 0),
        dna=None,
    ):
        super().__init__(model=model, space=space)

        self.position = position
        self.mutation_rate = mutation_rate
        self.duplication_rate = duplication_rate
        self.direction = np.array((1, 1), dtype=float)
        self.dna = dna if dna is not None else self.generate_dna()

    def step(self):
        if self.random.random() < self.duplication_rate:
            self.duplicate()
        self._random_move()

    def duplicate(self):
        VirusAgent(
            self.model,
            self.space,
            mutation_rate=self.mutation_rate,
            duplication_rate=self.duplication_rate,
            position=self.position,
            dna=self.generate_dna(self.dna),
        )

    def generate_dna(self, dna=None):
        if dna is None:
            return [self.random.randint(0, 9) for _ in range(3)]
        idx = self.random.randint(0, 2)
        chance = self.random.random()
        if chance < self.mutation_rate / 2:
            dna[idx] = (dna[idx] + 1) % 10
        elif chance < self.mutation_rate:
            dna[idx] = (dna[idx] - 1) % 10
        return dna
