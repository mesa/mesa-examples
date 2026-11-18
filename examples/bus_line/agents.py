"""Agents for the Bus Line model."""

import math

from mesa import Agent, Model
from mesa.experimental.actions import Action, HasActions
from mesa.experimental.mesa_signals import HasEmitters, Observable
from mesa.experimental.states import ContinuousState, Threshold


class Board(Action):
    """A passenger stepping onto the bus through its door.

    Boarding takes time, and the bus does not wait for it: if the doors close
    first, the bus interrupts the action and the passenger stays at the stop.
    The completion requirement re-checks that the doors are still open when the
    boarding time is up, so a boarding that ends at the very moment the bus
    leaves does not put the passenger on board.
    """

    def __init__(self, passenger: "Passenger", bus: "Bus", duration: float) -> None:
        """Create a boarding action.

        Args:
            passenger (Passenger): The passenger who boards.
            bus (Bus): The bus being boarded.
            duration (float): Time the passenger needs to board, seconds.
        """
        super().__init__(
            passenger,
            duration=duration,
            completion_requirements=lambda p: bus.doors_open_at == p.origin,
        )
        self.bus = bus

    def on_complete(self) -> None:
        """Take a seat and free the door for the next passenger."""
        self.bus.boarder = None
        self.agent.ride(self.bus)
        self.bus.board_next()

    def on_interrupt(self, progress: float) -> None:
        """Step back onto the stop when the doors close mid-boarding."""
        self.bus.boarder = None
        self.agent.status = "waiting"

    def on_fail(self) -> None:
        """Stay at the stop if the bus had already gone when boarding ended."""
        self.bus.boarder = None
        self.agent.status = "waiting"


class Passenger(Agent, HasActions):
    """A passenger who waits at a stop, boards the bus and rides to a destination.

    Attributes:
        origin (int): Index of the stop the passenger waits at.
        destination (int): Index of the stop the passenger rides to.
        status (str): "waiting", "boarding" or "riding".
        times_left_behind (int): How often the bus left this passenger's stop
            without them.
    """

    def __init__(self, model: Model, origin: int, destination: int) -> None:
        """Create a passenger waiting at a stop.

        Args:
            model (Model): The model instance that contains the passenger.
            origin (int): Index of the stop the passenger waits at.
            destination (int): Index of the stop the passenger rides to.
        """
        super().__init__(model)
        self.origin = origin
        self.destination = destination
        self.status = "waiting"
        self.times_left_behind = 0

    def start_boarding(self, bus: "Bus") -> None:
        """Step through the door of the bus at this passenger's stop.

        Args:
            bus (Bus): The bus at the stop.
        """
        self.status = "boarding"
        self.start_action(Board(self, bus, duration=self.model.boarding_time))

    def ride(self, bus: "Bus") -> None:
        """Ride the bus after boarding.

        Args:
            bus (Bus): The bus the passenger boarded.
        """
        self.status = "riding"
        bus.riders.add(self)


class Bus(Agent, HasEmitters):
    """A bus running a loop of stops, driven entirely by thresholds and events.

    Like the tram in Mesa's Tram Route Model, the bus accelerates to a cruise
    speed, coasts, brakes at an analytically computed point and stops, and each
    of those transitions is a threshold crossing. At each stop it opens its
    doors for a fixed dwell time: riders for that stop get off, and waiting
    passengers board one at a time through the door while there is room. When
    the dwell time is up the bus leaves, interrupting the passenger in the door
    and leaving everyone still waiting at the stop.

    Attributes:
        acceleration (Observable): Current acceleration, m/s^2.
        speed (ContinuousState): Current speed, m/s.
        position (ContinuousState): Distance travelled since the first stop, m.
        brake_point (Observable): Position at which braking begins for the
            current segment, m.
        cruise_speed (Observable): Speed at which the bus stops accelerating, m/s.
        doors_open_at (int | None): Index of the stop the bus is serving, or
            None while it is driving.
        riders (set[Passenger]): Passengers on board.
        boarder (Passenger | None): The passenger currently in the door.
    """

    acceleration = Observable(fallback_value=0.0)
    speed = ContinuousState(fallback_value=0.0, rate=lambda a: a.acceleration)
    position = ContinuousState(fallback_value=0.0, rate=lambda a: a.speed)
    brake_point = Observable(fallback_value=float("inf"))
    cruise_speed = Observable(fallback_value=12.0)

    # Named so they do not collide with the "_brake_point" and "_cruise_speed"
    # stores of the Observables they read (see the Tram Route Model).
    _cruise_threshold = Threshold(
        state=speed, limit=cruise_speed, callback="start_coasting", direction="rising"
    )
    _braking_threshold = Threshold(
        state=position, limit=brake_point, callback="brake", direction="rising"
    )
    _stop_threshold = Threshold(
        state=speed, limit=0.0, callback="arrive_at_stop", direction="falling"
    )

    def __init__(
        self,
        model: Model,
        n_stops: int,
        stop_spacing: float,
        capacity: int,
        dwell_time: float,
        cruise_speed: float = 12.0,
        acceleration_rate: float = 1.5,
        deceleration_rate: float = 2.0,
    ) -> None:
        """Create a bus at the first stop.

        Args:
            model (Model): The model instance that contains the bus.
            n_stops (int): Number of stops on the loop.
            stop_spacing (float): Distance between consecutive stops, m.
            capacity (int): Maximum number of passengers on board.
            dwell_time (float): Time the doors stay open at each stop, seconds.
            cruise_speed (float, optional): Target speed, m/s. Defaults to 12.0.
            acceleration_rate (float, optional): Acceleration when leaving a
                stop, m/s^2. Defaults to 1.5.
            deceleration_rate (float, optional): Deceleration when braking into
                a stop, m/s^2. Defaults to 2.0.

        Raises:
            ValueError: If there are fewer than two stops.
        """
        super().__init__(model)
        if n_stops < 2:
            raise ValueError("the loop needs at least two stops")

        self.n_stops = n_stops
        self.stop_spacing = stop_spacing
        self.capacity = capacity
        self.dwell_time = dwell_time
        self.acceleration_rate = acceleration_rate
        self.deceleration_rate = deceleration_rate
        self.stops_served = 0
        self.doors_open_at = None
        self.riders = set()
        self.boarder = None

        # The limits the thresholds read must exist before the first
        # ContinuousState assignment, which is what binds the thresholds.
        self.brake_point = float("inf")
        self.cruise_speed = cruise_speed

        self.acceleration = 0.0
        self.speed = 0.0
        self.position = 0.0

    @property
    def next_stop_position(self) -> float:
        """Position of the stop the bus is travelling towards.

        Returns:
            float: The target stop's position, m.
        """
        return (self.stops_served + 1) * self.stop_spacing

    def braking_distance(self) -> float:
        """Distance needed to stop from this segment's peak speed.

        On a short segment the bus cannot reach cruise speed before it must
        brake, so the peak speed is the triangular-profile one.

        Returns:
            float: The braking distance, m.
        """
        distance = self.next_stop_position - self.position
        triangular = math.sqrt(
            2.0
            * distance
            / (1.0 / self.acceleration_rate + 1.0 / self.deceleration_rate)
        )
        peak = min(self.cruise_speed, triangular)
        return peak**2 / (2.0 * self.deceleration_rate)

    def open_doors(self, stop: int) -> None:
        """Let riders for this stop off and start boarding.

        Args:
            stop (int): Index of the stop being served.
        """
        self.doors_open_at = stop
        alighting = sorted(
            (r for r in self.riders if r.destination == stop), key=lambda r: r.unique_id
        )
        for rider in alighting:
            self.riders.discard(rider)
            self.model.delivered += 1
            rider.remove()
        self.board_next()

    def board_next(self) -> None:
        """Let the next waiting passenger through the door, if there is room."""
        if self.doors_open_at is None or self.boarder is not None:
            return
        if len(self.riders) >= self.capacity:
            return
        waiting = self.model.waiting_at(self.doors_open_at)
        if waiting:
            self.boarder = waiting[0]
            self.boarder.start_boarding(self)

    def depart(self) -> None:
        """Close the doors and drive on, leaving anyone not yet on board."""
        stop = self.doors_open_at
        if self.boarder is not None:
            self.boarder.current_action.interrupt()
        for passenger in self.model.waiting_at(stop):
            passenger.times_left_behind += 1
            self.model.left_behind += 1
        self.doors_open_at = None
        self.brake_point = self.next_stop_position - self.braking_distance()
        self.acceleration = self.acceleration_rate

    def start_coasting(self) -> None:
        """Stop accelerating once cruise speed is reached."""
        self.acceleration = 0.0

    def brake(self) -> None:
        """Decelerate once the brake point for this segment is reached."""
        self.brake_point = float("inf")
        self.acceleration = -self.deceleration_rate

    def arrive_at_stop(self) -> None:
        """Stop, serve the stop and schedule the departure."""
        self.acceleration = 0.0
        self.stops_served += 1
        self.open_doors(self.stops_served % self.n_stops)
        self.model.schedule_event(self.depart, after=self.dwell_time)
