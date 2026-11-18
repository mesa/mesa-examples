"""Bus Line Model.

A bus runs a loop of stops in continuous time. Its kinematics follow Mesa's
Tram Route Model: every change of motion is a threshold crossing, so nothing
needs to be checked on every tick. Passengers arrive at random, board as a
timed, interruptible action, and are left behind when the doors close before
they finish boarding.
"""

from functools import partial

try:
    from .agents import Bus, Passenger
except ImportError:
    from agents import Bus, Passenger

from mesa import Model
from mesa.datacollection import DataCollector
from mesa.experimental.scenarios import Scenario


class BusLineScenario(Scenario):
    """Scenario for the Bus Line model.

    Args:
        n_stops: Number of stops on the loop.
        stop_spacing: Distance between consecutive stops, in meters.
        capacity: Maximum number of passengers on the bus.
        dwell_time: Time the doors stay open at each stop, in seconds.
        boarding_time: Time one passenger needs to board, in seconds.
        arrival_rate: Mean number of passengers arriving per stop per second.
        cruise_speed: Target speed of the bus, m/s.
        acceleration_rate: Acceleration when leaving a stop, m/s^2.
        deceleration_rate: Deceleration when braking into a stop, m/s^2.
        rng: Seed for reproducibility.
    """

    n_stops: int = 6
    stop_spacing: float = 300.0
    capacity: int = 30
    dwell_time: float = 15.0
    boarding_time: float = 3.0
    arrival_rate: float = 0.02
    cruise_speed: float = 12.0
    acceleration_rate: float = 1.5
    deceleration_rate: float = 2.0


class BusLine(Model):
    """A bus serving a loop of stops, with passengers arriving at random.

    Attributes:
        bus (Bus): The bus running the loop.
        boarding_time (float): Time one passenger needs to board, seconds.
        left_behind (int): Times the bus left a stop with passengers still
            waiting there, counted per passenger.
        delivered (int): Passengers who reached their destination.
    """

    def __init__(self, scenario: BusLineScenario = BusLineScenario):
        """Create the model, the bus and the first passenger arrivals.

        Args:
            scenario: BusLineScenario containing model parameters.
        """
        super().__init__(scenario=scenario)

        self.n_stops = int(scenario.n_stops)
        self.boarding_time = scenario.boarding_time
        self.arrival_rate = scenario.arrival_rate
        self.left_behind = 0
        self.delivered = 0

        self.bus = Bus(
            self,
            n_stops=self.n_stops,
            stop_spacing=scenario.stop_spacing,
            capacity=int(scenario.capacity),
            dwell_time=scenario.dwell_time,
            cruise_speed=scenario.cruise_speed,
            acceleration_rate=scenario.acceleration_rate,
            deceleration_rate=scenario.deceleration_rate,
        )

        self.datacollector = DataCollector(
            model_reporters={
                "Speed": lambda m: m.bus.speed,
                "Waiting": lambda m: len(m.waiting_passengers()),
                "On board": lambda m: len(m.bus.riders),
                "Left behind": lambda m: m.left_behind,
                "Delivered": lambda m: m.delivered,
            }
        )
        self.datacollector.collect(self)

        # Every arrival schedules the next one at the same stop, so each stop
        # receives a Poisson stream of passengers without any per-step work.
        # Events hold their callback weakly, so the per-stop callbacks are kept
        # here for as long as the model lives.
        self._arrival_callbacks = [
            partial(self.passenger_arrives, stop) for stop in range(self.n_stops)
        ]
        if self.arrival_rate > 0:
            for stop in range(self.n_stops):
                self.schedule_next_arrival(stop)

        # The bus starts at the first stop with its doors open.
        self.schedule_event(self.start_service, at=0.0)

    def start_service(self) -> None:
        """Serve the first stop and schedule the bus's first departure."""
        self.bus.open_doors(0)
        self.schedule_event(self.bus.depart, after=self.bus.dwell_time)

    def passenger_arrives(self, stop: int) -> None:
        """Add a passenger at a stop and schedule the stop's next arrival.

        A passenger who arrives while the bus is at the stop joins the queue
        for the door.

        Args:
            stop (int): Index of the stop the passenger arrives at.
        """
        offset = int(self.rng.integers(1, self.n_stops))
        Passenger(self, origin=stop, destination=(stop + offset) % self.n_stops)
        if self.bus.doors_open_at == stop:
            self.bus.board_next()
        self.schedule_next_arrival(stop)

    def schedule_next_arrival(self, stop: int) -> None:
        """Schedule the next passenger arrival at a stop.

        Args:
            stop (int): Index of the stop.
        """
        self.schedule_event(
            self._arrival_callbacks[stop],
            after=self.rng.exponential(1.0 / self.arrival_rate),
        )

    def waiting_passengers(self) -> list[Passenger]:
        """Passengers waiting at any stop.

        Returns:
            list[Passenger]: The waiting passengers.
        """
        return [
            p for p in self.agents_by_type.get(Passenger, []) if p.status == "waiting"
        ]

    def waiting_at(self, stop: int) -> list[Passenger]:
        """Passengers waiting at a stop, in creation order.

        Args:
            stop (int): Index of the stop.

        Returns:
            list[Passenger]: The passengers waiting there.
        """
        waiting = [p for p in self.waiting_passengers() if p.origin == stop]
        return sorted(waiting, key=lambda p: p.unique_id)

    def step(self) -> None:
        """Sample the model once per time unit for the plots.

        The bus and the passengers need no per-step logic: motion is
        extrapolated analytically, transitions fire from thresholds, and
        boarding completes or is interrupted on the event queue.
        """
        self.datacollector.collect(self)


if __name__ == "__main__":
    model = BusLine(scenario=BusLineScenario())
    model.run_until(1800.0)
    print(f"Final time:      {model.time:.1f} s")
    print(f"Stops served:    {model.bus.stops_served}")
    print(f"Delivered:       {model.delivered}")
    print(f"On board:        {len(model.bus.riders)}")
    print(f"Waiting:         {len(model.waiting_passengers())}")
    print(f"Left behind:     {model.left_behind}")
