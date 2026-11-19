from __future__ import annotations

from mesa import Agent, Model
from mesa.experimental.actions import Action, ActionState, HasActions


class Machine(HasActions, Agent):
    def __init__(self, model: Model):
        super().__init__(model)

        self.is_broken = False
        self.interrupted_job: Action | None = None

    def breakdown(self) -> None:
        """Interrupt production and initiate machine repair."""

        if self.is_broken:
            return

        print(f"[t={self.model.time}] Breakdown triggered")

        self.is_broken = True

        current = self.current_action

        if isinstance(current, ProductionAction):
            self.interrupted_job = current

        repair_action = RepairAction(self)
        self.interrupt_for(repair_action)

    def on_idle(self, previous: Action) -> None:
        """Resume interrupted production when the machine becomes idle."""

        if (
            isinstance(previous, RepairAction)
            and previous.state == ActionState.COMPLETED
            and self.interrupted_job is not None
            and not self.is_broken
        ):
            job = self.interrupted_job
            self.interrupted_job = None
            self.start_action(job)


class ActionPriority:
    PRODUCTION = 1
    REPAIR = 10


class ProductionAction(Action):
    """Represents a production job executed by a machine."""

    def __init__(self, machine: Machine, duration: float, job_name: str):
        super().__init__(
            machine,
            duration=duration,
            name=f"Production: {job_name}",
            priority=ActionPriority.PRODUCTION,
            interruptible=True,
        )

        self.job_name = job_name

    def on_complete(self) -> None:
        """Called when production finishes."""
        print(f"{self.job_name} completed by Machine {self.agent.unique_id}")

    def on_start(self):
        print(f"[t={self.model.time}] {self.job_name} started")

    def on_resume(self):
        print(f"[t={self.model.time}] {self.job_name} resumed at {self.progress:.0%}")

    def on_interrupt(self, progress):
        print(f"[t={self.model.time}] {self.job_name} interrupted at {progress:.0%}")


class RepairAction(Action):
    """Represents the repair process for a broken machine."""

    def __init__(self, machine: Machine, duration: float = 3.0):
        super().__init__(
            machine,
            duration=duration,
            name="Machine Repair",
            priority=ActionPriority.REPAIR,
            interruptible=False,
        )

    def on_start(self) -> None:
        """Begin repairing the broken machine."""
        self.agent.is_broken = True
        print(f"Machine {self.agent.unique_id} repair started.")

    def on_complete(self) -> None:
        """Mark the machine as operational after repair."""
        self.agent.is_broken = False
        print(f"Machine {self.agent.unique_id} has been repaired.")
