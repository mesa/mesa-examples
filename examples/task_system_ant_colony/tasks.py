"""
Task system for Mesa agents.

Implements the Task concept proposed in Mesa discussion #2526 (EwoutH).
A Task represents an activity an agent performs over time -- with explicit
duration, priority, progress tracking, interruptibility, and a pluggable
reward function.

This is the missing execution layer between "agent decides what to do"
and "agent actually does it over multiple steps."
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
from collections.abc import Callable


class TaskStatus(Enum):
    PENDING = auto()  # Queued, not yet started
    ACTIVE = auto()  # Currently being executed
    INTERRUPTED = auto()  # Paused mid-execution
    DONE = auto()  # Completed, reward already applied
    FAILED = auto()  # Could not complete (requirements unmet)


def linear_reward(progress: float) -> float:
    """50% completion → 50% reward. Simple and fair."""
    return progress


def threshold_reward(progress: float, threshold: float = 1.0) -> float:
    """No reward until threshold reached. All-or-nothing by default."""
    return 1.0 if progress >= threshold else 0.0


def exponential_reward(progress: float) -> float:
    """Reward accelerates near completion. y = x^2."""
    return progress**2


@dataclass
class Task:
    """
    A Task represents a specific activity an agent performs over time.

    Core properties (from discussion #2526):
      - duration:      How many steps to complete (int = step-based)
      - priority:      Higher number = higher priority. Used by TaskQueue.
      - reward_fn:     Called with progress [0.0-1.0] → float reward value
      - interruptible: Can another agent or event pause this?
      - resumable:     If interrupted, can it continue from where it left off?

    Example usage:
        dig = Task(name="Dig Soil", duration=5, priority=10, reward_fn=linear_reward)
        agent.task_queue.push(dig)
    """

    name: str
    duration: int  # Steps needed to complete
    priority: int = 0  # Higher = more urgent
    reward_fn: Callable[[float], float] = field(default=linear_reward)
    interruptible: bool = True
    resumable: bool = True

    # Runtime state (set by TaskQueue, not by user)
    status: TaskStatus = field(default=TaskStatus.PENDING, init=False)
    progress: int = field(default=0, init=False)  # Steps completed so far

    @property
    def completion(self) -> float:
        """Progress as a fraction [0.0 - 1.0]."""
        if self.duration == 0:
            return 1.0
        return min(self.progress / self.duration, 1.0)

    @property
    def is_complete(self) -> bool:
        return self.progress >= self.duration

    @property
    def reward(self) -> float:
        """Current reward based on progress. Call after completion or interruption."""
        return self.reward_fn(self.completion)

    def step(self) -> float:
        """
        Advance the task by one simulation step.
        Returns reward if task just completed, else 0.
        """
        if self.status != TaskStatus.ACTIVE:
            return 0.0

        self.progress += 1

        if self.is_complete:
            self.status = TaskStatus.DONE
            return self.reward

        return 0.0

    def interrupt(self) -> float:
        """
        Interrupt this task. Returns partial reward if interruptible.
        Raises RuntimeError if not interruptible.
        """
        if not self.interruptible:
            raise RuntimeError(f"Task '{self.name}' cannot be interrupted.")
        self.status = TaskStatus.INTERRUPTED
        return self.reward  # Partial reward based on progress so far

    def resume(self):
        """Resume an interrupted task if it is resumable."""
        if self.status != TaskStatus.INTERRUPTED:
            raise RuntimeError(f"Task '{self.name}' is not interrupted, cannot resume.")
        if not self.resumable:
            self.progress = 0  # Start over
        self.status = TaskStatus.ACTIVE


class TaskQueue:
    """
    Priority queue of Tasks for a single agent.

    Manages the full task lifecycle:
      - push():   Add a new task
      - step():   Advance the active task by one step
      - interrupt(): Force-interrupt the current task (e.g. pheromone signal)
      - current:  The active task, or None

    The agent calls task_queue.step() inside its own step() method.
    The queue handles status transitions automatically.
    """

    def __init__(self):
        self._queue: list[Task] = []
        self.current: Task | None = None
        self.total_reward: float = 0.0

    def push(self, task: Task):
        """Add a task. Automatically sorted by priority (highest first)."""
        self._queue.append(task)
        self._queue.sort(key=lambda t: t.priority, reverse=True)

    def step(self) -> float:
        """
        One simulation step:
          1. If no active task, pick the highest-priority pending one.
          2. Advance it by one step.
          3. If it completes, collect reward and move to next.
        Returns reward earned this step (0 if none).
        """
        # Promote from queue if idle
        if self.current is None or self.current.status in (
            TaskStatus.DONE,
            TaskStatus.FAILED,
        ):
            self._activate_next()

        if self.current is None:
            return 0.0  # Nothing to do

        reward = self.current.step()
        self.total_reward += reward
        return reward

    def interrupt_current(self, force: bool = False) -> float | None:
        """
        Interrupt the active task.
        If force=True, interrupts even non-interruptible tasks (sets FAILED).
        Returns partial reward, or None if no active task.
        """
        if self.current is None or self.current.status != TaskStatus.ACTIVE:
            return None

        if not self.current.interruptible and not force:
            return None  # Can't interrupt, silently ignore

        if force and not self.current.interruptible:
            self.current.status = TaskStatus.FAILED
            return 0.0

        partial = self.current.interrupt()
        self.total_reward += partial

        if self.current.resumable:
            # Put it back in the queue so it can resume
            self._queue.append(self.current)
            self._queue.sort(key=lambda t: t.priority, reverse=True)

        self.current = None
        return partial

    def _activate_next(self):
        """Pull the highest-priority pending task and activate it."""
        pending = [t for t in self._queue if t.status == TaskStatus.PENDING]
        if not pending:
            self.current = None
            return
        # Already sorted by priority
        self.current = pending[0]
        self._queue.remove(self.current)
        self.current.status = TaskStatus.ACTIVE

    def __len__(self):
        return len(self._queue) + (1 if self.current else 0)

    def __repr__(self):
        return (
            f"TaskQueue(current={self.current.name if self.current else None}, "
            f"queued={len(self._queue)}, total_reward={self.total_reward:.2f})"
        )
