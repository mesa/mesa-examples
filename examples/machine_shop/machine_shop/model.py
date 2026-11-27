"""Machine Shop simulation model."""

from mesa import Model

from .agents import (
    Machine,
    ProductionAction,
)


class MachineShop(Model):
    """A machine shop with production and breakdowns."""

    def __init__(self):
        super().__init__()

        self.machine = Machine(self)

        self.production = ProductionAction(
            self.machine,
            duration=10,
            job_name="Job A",
        )

        self.machine.start_action(self.production)

        self.schedule_event(
            self.machine.breakdown,
            after=4,
        )

        self.schedule_event(
            self.machine.breakdown,
            at=9,
        )
