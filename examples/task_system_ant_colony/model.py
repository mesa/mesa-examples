"""
Ant Colony model demonstrating the Mesa Task System (discussion #2526).

What this demonstrates:
  - Agents with a TaskQueue executing tasks over multiple steps
  - Task interruption via pheromone signals (high-priority event)
  - Task resumption after interruption
  - Pluggable reward functions (linear for digging, threshold for transport)
  - Emergent colony behavior from individual task priorities

Scenario:
  Ants build a nest by cycling through three tasks:
    1. Dig Soil      (duration=5, priority=10, linear reward, interruptible)
    2. Transport     (duration=3, priority=8,  threshold reward, interruptible)
    3. Rest          (duration=2, priority=1,  linear reward, resumable)

  Any ant can emit an URGENT pheromone signal (cave-in event). Every ant
  within signal_radius that is performing an interruptible task will drop it
  and immediately start a "Respond to Signal" task (priority=100).
"""

import mesa
import numpy as np
from tasks import Task, TaskQueue, linear_reward, threshold_reward

# ── Task factories ──────────────────────────────────────────────────────────


def make_dig_task() -> Task:
    return Task(
        name="Dig Soil",
        duration=5,
        priority=10,
        reward_fn=linear_reward,
        interruptible=True,
        resumable=True,
    )


def make_transport_task() -> Task:
    return Task(
        name="Transport Material",
        duration=3,
        priority=8,
        reward_fn=lambda p: threshold_reward(p, threshold=1.0),
        interruptible=True,
        resumable=False,
    )


def make_rest_task() -> Task:
    return Task(
        name="Rest",
        duration=2,
        priority=1,
        reward_fn=linear_reward,
        interruptible=True,
        resumable=True,
    )


def make_urgent_task() -> Task:
    return Task(
        name="Respond to Signal",
        duration=2,
        priority=100,
        reward_fn=linear_reward,
        interruptible=False,
        resumable=False,
    )


# ── Agent ─────────────────────────────────────────────────────────────────────


class AntAgent(mesa.Agent):
    def __init__(self, model):
        super().__init__(model)
        self.task_queue = TaskQueue()
        self.interrupted_count: int = 0
        self._refill_queue()

    def _refill_queue(self):
        self.task_queue.push(make_dig_task())
        self.task_queue.push(make_transport_task())
        self.task_queue.push(make_rest_task())

    def step(self):
        if self._detect_pheromone_signal():
            partial = self.task_queue.interrupt_current()
            if partial is not None:
                self.interrupted_count += 1
            self.task_queue.push(make_urgent_task())

        self.task_queue.step()

        if len(self.task_queue) == 0:
            self._refill_queue()

    def _detect_pheromone_signal(self) -> bool:
        pos = self.pos
        if pos is None:
            return False
        x, y = pos
        radius = self.model.signal_radius
        grid = self.model.pheromone_grid
        width, height = self.model.grid.width, self.model.grid.height
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                nx, ny = (x + dx) % width, (y + dy) % height
                if grid[nx, ny] > 0:
                    return True
        return False

    @property
    def current_task_name(self) -> str:
        if self.task_queue.current is None:
            return "Idle"
        return self.task_queue.current.name

    @property
    def current_task_progress(self) -> float:
        if self.task_queue.current is None:
            return 0.0
        return self.task_queue.current.completion


# ── Model ─────────────────────────────────────────────────────────────────────


class AntColonyModel(mesa.Model):
    def __init__(
        self,
        n_ants=20,
        width=20,
        height=20,
        signal_radius=3,
        signal_prob=0.05,
        seed=None,
    ):
        super().__init__(seed=seed)
        self.n_ants = n_ants
        self.signal_radius = signal_radius
        self.signal_prob = signal_prob

        self.grid = mesa.space.MultiGrid(width, height, torus=True)
        self.pheromone_grid = np.zeros((width, height), dtype=float)

        for _ in range(n_ants):
            ant = AntAgent(self)
            x = self.random.randrange(width)
            y = self.random.randrange(height)
            self.grid.place_agent(ant, (x, y))

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Total Reward": lambda m: sum(
                    a.task_queue.total_reward for a in m.agents
                ),
                "Ants Digging": lambda m: sum(
                    1 for a in m.agents if a.current_task_name == "Dig Soil"
                ),
                "Ants Transporting": lambda m: sum(
                    1 for a in m.agents if a.current_task_name == "Transport Material"
                ),
                "Ants Responding": lambda m: sum(
                    1 for a in m.agents if a.current_task_name == "Respond to Signal"
                ),
                "Ants Resting": lambda m: sum(
                    1 for a in m.agents if a.current_task_name == "Rest"
                ),
                "Total Interruptions": lambda m: sum(
                    a.interrupted_count for a in m.agents
                ),
            },
            agent_reporters={
                "Task": "current_task_name",
                "Progress": "current_task_progress",
                "Total Reward": lambda a: a.task_queue.total_reward,
                "Interruptions": "interrupted_count",
            },
        )
        self.datacollector.collect(self)

    def step(self):
        self.pheromone_grid *= 0.7
        self.pheromone_grid[self.pheromone_grid < 0.01] = 0.0

        if self.random.random() < self.signal_prob:
            cx = self.random.randrange(self.grid.width)
            cy = self.random.randrange(self.grid.height)
            self.pheromone_grid[cx, cy] = 1.0

        self.agents.shuffle_do("step")
        self.datacollector.collect(self)
