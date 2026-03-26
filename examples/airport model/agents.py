# agents.py
from mesa import Agent


class AircraftAgent(Agent):
    def __init__(
        self,
        model,
        flight_id: str,
        flight_type: str,   # "inbound" or "outbound"
        fuel_remaining: int | None = None,
        emergency: bool = False,
    ):
        super().__init__(model)
        self.flight_id = flight_id
        self.flight_type = flight_type
        self.fuel_remaining = fuel_remaining
        self.emergency = emergency

        self.status = "scheduled"  # scheduled, holding, takeoff_queue, landing, takeoff, landed, departed, diverted, cancelled
        self.wait_time = 0
        self.assigned_runway = None
        self.arrival_order = None

    def step(self):
        # Aircraft logic is mostly passive in this model.
        # The model coordinates queues and runway assignment.
        if self.status in {"holding", "takeoff_queue"}:
            self.wait_time += self.model.tick_size

        if self.flight_type == "inbound" and self.status == "holding":
            self.consume_fuel()

    def consume_fuel(self):
        if self.fuel_remaining is None:
            return

        self.fuel_remaining -= self.model.tick_size

        if self.fuel_remaining <= self.model.minimum_fuel_threshold:
            self.status = "diverted"
            self.model.divert_aircraft(self)

        elif self.fuel_remaining <= self.model.emergency_fuel_threshold:
            self.emergency = True


# agents.py
class RunwayAgent(Agent):
    def __init__(self, model, runway_id: str, mode: str = "mixed"):
        super().__init__(model)
        self.runway_id = runway_id
        self.mode = mode   # "landing", "takeoff", "mixed"
        self.blocked = False
        self.current_aircraft = None
        self.remaining_service_time = 0
        self.operation = None  # "landing" or "takeoff"

    def is_available_for(self, operation: str) -> bool:
        if self.blocked:
            return False
        if self.current_aircraft is not None:
            return False
        if self.mode == "mixed":
            return True
        return self.mode == operation

    def assign(self, aircraft, operation: str, duration: int):
        self.current_aircraft = aircraft
        self.operation = operation
        self.remaining_service_time = duration
        aircraft.assigned_runway = self.runway_id
        aircraft.status = operation

    def step(self):
        if self.current_aircraft is None:
            return

        self.remaining_service_time -= self.model.tick_size

        if self.remaining_service_time <= 0:
            aircraft = self.current_aircraft

            if self.operation == "landing":
                aircraft.status = "landed"
                self.model.landed_count += 1
            else:
                aircraft.status = "departed"
                self.model.departed_count += 1

            aircraft.assigned_runway = None
            self.current_aircraft = None
            self.operation = None
            self.remaining_service_time = 0