"""Elevator Bank model.

A bank of elevator cars serves hall calls in a building, in continuous time.
Each car's height and velocity are chained continuous states and every
transition of a trip -- reaching cruise speed, starting to brake, coming to
rest -- is a Threshold crossing solved analytically and scheduled once. Hall
calls arrive as events; when a call lands on a floor ahead of a moving car,
the dispatcher rewrites that car's reactive brake point and the car stops
there without any per-tick polling.
"""

from mesa import Model
from mesa.datacollection import DataCollector
from mesa.experimental.data_collection import DataRecorder
from mesa.experimental.scenarios import Scenario

try:
    from .agents import Call, ElevatorCar
except ImportError:
    from agents import Call, ElevatorCar


class ElevatorScenario(Scenario):
    """Scenario for the Elevator Bank model.

    Args:
        n_floors: Number of floors, ground floor included.
        n_cars: Number of cars in the bank.
        floor_height: Distance between floors, in meters.
        max_speed: Cruise speed of a car, m/s.
        acceleration_rate: Acceleration and braking rate, m/s^2.
        door_time: Seconds a car spends at a floor with its doors open.
        mean_call_gap: Mean time between hall calls, in seconds.
        rng: Seed for reproducibility.
    """

    n_floors: int = 12
    n_cars: int = 2
    floor_height: float = 3.5
    max_speed: float = 2.5
    acceleration_rate: float = 1.0
    door_time: float = 8.0
    mean_call_gap: float = 25.0


class ElevatorBank(Model):
    """A bank of cars answering hall calls.

    Attributes:
        cars (list[ElevatorCar]): The cars in the bank.
        waiting (list[Call]): Calls not yet answered, oldest first. A call stays
            here while a car is on its way to it.
        wait_times (list[float]): Time each answered call waited, in seconds.
    """

    def __init__(self, scenario: ElevatorScenario = ElevatorScenario):
        """Create the building, its cars and the first hall call.

        Args:
            scenario: ElevatorScenario containing model parameters.
        """
        super().__init__(scenario=scenario)

        self.n_floors = int(scenario.n_floors)
        self.mean_call_gap = scenario.mean_call_gap
        self.waiting: list[Call] = []
        self.wait_times: list[float] = []
        self.calls_placed = 0

        n_cars = int(scenario.n_cars)
        self.cars = [
            ElevatorCar(
                self,
                floor_height=scenario.floor_height,
                max_speed=scenario.max_speed,
                acceleration_rate=scenario.acceleration_rate,
                door_time=scenario.door_time,
                # Spread the cars over the building to begin with.
                start_floor=round(i * (self.n_floors - 1) / (n_cars - 1))
                if n_cars > 1
                else 0,
            )
            for i in range(n_cars)
        ]

        self.recorder = DataRecorder(self)
        self.data_registry.track_agents(
            self.agents, "car_data", ["height", "velocity", "acceleration"]
        ).record(self.recorder)

        # The DataCollector is kept alongside only to feed the plots in app.py.
        self.datacollector = DataCollector(
            model_reporters={
                "Waiting calls": lambda m: len(m.waiting),
                "Mean wait (s)": lambda m: (
                    sum(m.wait_times) / len(m.wait_times) if m.wait_times else 0.0
                ),
            }
        )
        self.datacollector.collect(self)

        self.schedule_event(self.place_call, after=self.next_call_gap())

    # --- hall calls ---------------------------------------------------------

    def next_call_gap(self) -> float:
        """Seconds until the next hall call, exponentially distributed."""
        return float(self.rng.exponential(self.mean_call_gap))

    def place_call(self) -> None:
        """Someone presses a hall button; then schedule the next press."""
        floor = int(self.rng.integers(0, self.n_floors))
        call = Call(floor, self.time)
        self.calls_placed += 1
        self.waiting.append(call)
        self.dispatch(call)
        self.schedule_event(self.place_call, after=self.next_call_gap())

    def dispatch(self, call: Call) -> None:
        """Send a car to `call` if one is free for it.

        A car already heading for that floor answers it on arrival. A moving car
        that passes the floor and can still stop there is re-targeted: that only
        rewrites its ``brake_point`` and the braking threshold re-solves itself;
        its previous target stays in ``waiting`` and is picked up afterwards.
        Otherwise the nearest idle car departs. If every car is busy the call
        simply waits in the queue.
        """
        if any(car.target_floor == call.floor for car in self.cars):
            return

        passing = [
            car
            for car in self.cars
            if car.moving
            and (car.target_floor - call.floor) * car.direction > 0
            and car.can_stop_at(call.floor)
        ]
        if passing:
            min(passing, key=lambda c: c.distance_to(call.floor)).go_to(call.floor)
            return

        idle = [car for car in self.cars if car.idle]
        if idle:
            min(idle, key=lambda c: c.distance_to(call.floor)).go_to(call.floor)

    def calls_answered(self, car: ElevatorCar, floor: int) -> int:
        """Record every waiting call for `floor` as answered. Returns the count."""
        answered = [call for call in self.waiting if call.floor == floor]
        for call in answered:
            self.waiting.remove(call)
            self.wait_times.append(self.time - call.placed_at)
        return len(answered)

    def car_available(self, car: ElevatorCar) -> None:
        """A car closed its doors: give it the oldest call nobody is heading to."""
        targeted = {c.target_floor for c in self.cars if c.target_floor is not None}
        for call in self.waiting:
            if call.floor not in targeted:
                car.go_to(call.floor)
                return

    def step(self) -> None:
        """Sample the model once per time unit for the plots.

        Nothing here drives the cars: their trips run entirely off the
        thresholds and the event queue, and deleting this method changes no
        timing.
        """
        self.datacollector.collect(self)


if __name__ == "__main__":
    model = ElevatorBank(scenario=ElevatorScenario(rng=42))
    model.run_until(3600.0)

    print(f"Calls placed: {model.calls_placed}, answered: {len(model.wait_times)}")
    if model.wait_times:
        print(f"Mean wait: {sum(model.wait_times) / len(model.wait_times):.1f} s")
    for i, car in enumerate(model.cars):
        print(f"Car {i}: floor {car.floor:.2f}, served {car.served} calls")
    print(model.recorder.get_table_dataframe("car_data").tail(6).to_string())
