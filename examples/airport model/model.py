# model.py
from mesa import Model
from mesa.datacollection import DataCollector

from agents import AircraftAgent, RunwayAgent
from queues import HoldingQueue, TakeOffQueue
import numpy as np


class AirportModel(Model):
    def __init__(
        self,
        num_runways: int = 2,
        inbound_rate: int = 12,              # aircraft per hour
        outbound_rate: int = 10,             # aircraft per hour
        tick_size: int = 1,                  # minutes per step
        emergency_fuel_threshold: int = 30,  # minutes of fuel remaining
        minimum_fuel_threshold: int = 20,    # diversion threshold
        max_takeoff_wait: int = 45,          # cancellation threshold
        landing_duration: int = 3,           # minutes runway occupied
        takeoff_duration: int = 2,           # minutes runway occupied
        emergency_probability: float = 0.01,
        seed=None,
    ):
        super().__init__(seed=seed)

        # Core simulation parameters
        self.tick_size = tick_size
        self.inbound_rate = inbound_rate
        self.outbound_rate = outbound_rate
        self.emergency_fuel_threshold = emergency_fuel_threshold
        self.minimum_fuel_threshold = minimum_fuel_threshold
        self.max_takeoff_wait = max_takeoff_wait
        self.landing_duration = landing_duration
        self.takeoff_duration = takeoff_duration
        self.emergency_probability = emergency_probability

        # Timekeeping
        self.tick_count = 0
        self.sim_time = 0  # in minutes

        # Domain queues
        self.holding_queue = HoldingQueue()
        self.takeoff_queue = TakeOffQueue()

        # Counters
        self.flight_counter = 0
        self.inbound_accumulator = 0.0
        self.outbound_accumulator = 0.0

        # Outcome statistics
        self.landed_count = 0
        self.departed_count = 0
        self.diverted_count = 0
        self.cancelled_count = 0
        self.max_consecutive_landings = 3
        self.consecutive_landings = 0
        self.max_holding_queue_size = 0
        self.max_takeoff_queue_size = 0
        self.sum_holding_queue_size = 0
        self.sum_takeoff_queue_size = 0
        self.max_holding_wait_seen = 0
        self.max_takeoff_wait_seen = 0

        # Runway resources
        self.runways = [
            RunwayAgent(self, runway_id=f"RWY-{i + 1}", mode="mixed")
            for i in range(num_runways)
        ]

        # Data collection
        self.datacollector = DataCollector(
            model_reporters={
                "time": lambda m: m.sim_time,
                "holding_queue_size": lambda m: len(m.holding_queue),
                "takeoff_queue_size": lambda m: len(m.takeoff_queue),
                "landed": "landed_count",
                "departed": "departed_count",
                "diverted": "diverted_count",
                "cancelled": "cancelled_count",
                "avg_wait_time": lambda m: m.average_wait_time(),
            },
            agent_reporters={
                "status": lambda a: getattr(a, "status", None),
                "wait_time": lambda a: getattr(a, "wait_time", None),
                "emergency": lambda a: getattr(a, "emergency", None),
                "flight_type": lambda a: getattr(a, "flight_type", None),
            },
        )

    def next_flight_id(self) -> str:
        self.flight_counter += 1
        return f"FLT-{self.flight_counter:04d}"

    def average_wait_time(self) -> float:
        aircraft_agents = [
            agent for agent in self.agents if isinstance(agent, AircraftAgent)
        ]
        if not aircraft_agents:
            return 0.0
        return sum(agent.wait_time for agent in aircraft_agents) / len(aircraft_agents)

    def create_inbound_aircraft(self) -> None:
        emergency = self.random.random() < self.emergency_probability
        fuel = self.random.randint(35, 90)

        aircraft = AircraftAgent(
            self,
            flight_id=self.next_flight_id(),
            flight_type="inbound",
            fuel_remaining=fuel,
            emergency=emergency,
        )
        aircraft.status = "holding"

        # Mesa registers the agent on creation; queue tracks domain ordering
        self.holding_queue.enqueue(aircraft, self.sim_time)

    def create_outbound_aircraft(self) -> None:
        aircraft = AircraftAgent(
            self,
            flight_id=self.next_flight_id(),
            flight_type="outbound",
            fuel_remaining=None,
            emergency=False,
        )
        aircraft.status = "takeoff_queue"
        self.takeoff_queue.enqueue(aircraft, self.sim_time)

    def generate_aircraft(self) -> None:
        inbound_lambda = self.inbound_rate * (self.tick_size / 60)
        outbound_lambda = self.outbound_rate * (self.tick_size / 60)

        inbound_count = np.random.poisson(inbound_lambda)
        outbound_count = np.random.poisson(outbound_lambda)

        for _ in range(inbound_count):
            self.create_inbound_aircraft()

        for _ in range(outbound_count):
            self.create_outbound_aircraft()

    def divert_aircraft(self, target_aircraft: AircraftAgent) -> None:
        if target_aircraft.status != "diverted":
            target_aircraft.status = "diverted"

        self.diverted_count += 1

        rebuilt_queue = HoldingQueue()

        while len(self.holding_queue) > 0:
            item = self.holding_queue.dequeue_with_order()
            if item is None:
                break

            _, order, aircraft = item
            if aircraft is target_aircraft:
                continue

            rebuilt_queue.enqueue_with_order(aircraft, self.sim_time, order)

        self.holding_queue = rebuilt_queue

    def cancel_overdue_takeoffs(self) -> None:
        rebuilt_queue = TakeOffQueue()

        while not self.takeoff_queue.isEmpty():
            aircraft = self.takeoff_queue.dequeue()
            if aircraft is None:
                break

            if aircraft.wait_time > self.max_takeoff_wait:
                aircraft.status = "cancelled"
                self.cancelled_count += 1
            else:
                rebuilt_queue.enqueue(aircraft, self.sim_time)

        self.takeoff_queue = rebuilt_queue

    def refresh_holding_priorities(self) -> None:
        rebuilt_queue = HoldingQueue()

        while len(self.holding_queue) > 0:
            item = self.holding_queue.dequeue_with_order()
            if item is None:
                break

            _, order, aircraft = item

            if aircraft.status == "holding":
                rebuilt_queue.enqueue_with_order(aircraft, self.sim_time, order)

        self.holding_queue = rebuilt_queue

    def assign_runways(self) -> None:
        for runway in self.runways:
            if runway.current_aircraft is not None or runway.blocked:
                continue

            holding_has_aircraft = len(self.holding_queue) > 0
            takeoff_has_aircraft = len(self.takeoff_queue) > 0

            if not holding_has_aircraft and not takeoff_has_aircraft:
                continue

            # Emergency landing always wins
            next_holding = self.holding_queue.peek() if holding_has_aircraft else None
            if (
                    next_holding is not None
                    and next_holding.emergency
                    and runway.is_available_for("landing")
            ):
                aircraft = self.holding_queue.dequeue()
                runway.assign(
                    aircraft,
                    operation="landing",
                    duration=self.landing_duration,
                )
                self.consecutive_landings += 1
                continue

            # Fairness policy: after too many consecutive landings, allow a takeoff
            if (
                    takeoff_has_aircraft
                    and self.consecutive_landings >= self.max_consecutive_landings
                    and runway.is_available_for("takeoff")
            ):
                aircraft = self.takeoff_queue.dequeue()
                runway.assign(
                    aircraft,
                    operation="takeoff",
                    duration=self.takeoff_duration,
                )
                self.consecutive_landings = 0
                continue

            # Otherwise prefer landing if available
            if holding_has_aircraft and runway.is_available_for("landing"):
                aircraft = self.holding_queue.dequeue()
                runway.assign(
                    aircraft,
                    operation="landing",
                    duration=self.landing_duration,
                )
                self.consecutive_landings += 1
                continue

            if takeoff_has_aircraft and runway.is_available_for("takeoff"):
                aircraft = self.takeoff_queue.dequeue()
                runway.assign(
                    aircraft,
                    operation="takeoff",
                    duration=self.takeoff_duration,
                )
                self.consecutive_landings = 0

    def step(self) -> None:
        # 1. Update aircraft state
        for agent in list(self.agents):
            if isinstance(agent, AircraftAgent):
                agent.step()

        # 2. Update runway state
        for runway in self.runways:
            runway.step()

        # 3. Generate new traffic
        self.generate_aircraft()

        # 4. Recompute priorities and constraints
        self.refresh_holding_priorities()
        self.cancel_overdue_takeoffs()

        # 5. Assign available runways
        self.assign_runways()

        # 6. Collect data
        self.datacollector.collect(self)

        # 7. Advance time
        self.tick_count += 1
        self.sim_time += self.tick_size
        self.update_statistics()

    def update_statistics(self) -> None:
        holding_size = len(self.holding_queue)
        takeoff_size = len(self.takeoff_queue)

        self.max_holding_queue_size = max(self.max_holding_queue_size, holding_size)
        self.max_takeoff_queue_size = max(self.max_takeoff_queue_size, takeoff_size)

        self.sum_holding_queue_size += holding_size
        self.sum_takeoff_queue_size += takeoff_size

        holding_snapshot = self.holding_queue.to_list()
        takeoff_snapshot = self.takeoff_queue.to_list()

        if holding_snapshot:
            self.max_holding_wait_seen = max(
                self.max_holding_wait_seen,
                max(a.wait_time for a in holding_snapshot)
            )

        if takeoff_snapshot:
            self.max_takeoff_wait_seen = max(
                self.max_takeoff_wait_seen,
                max(a.wait_time for a in takeoff_snapshot)
            )

    def avg_holding_queue_size(self) -> float:
        return self.sum_holding_queue_size / max(1, self.tick_count)

    def avg_takeoff_queue_size(self) -> float:
        return self.sum_takeoff_queue_size / max(1, self.tick_count)