"""Agents for the Elevator Bank model."""

import math

from mesa import Agent, Model
from mesa.experimental.mesa_signals import HasEmitters, Observable
from mesa.experimental.states import ContinuousState, Threshold

INF = float("inf")


class Call:
    """A request for a car to come to a floor.

    Attributes:
        floor (int): The floor the call was made from.
        placed_at (float): Model time at which the button was pressed.
    """

    def __init__(self, floor: int, placed_at: float) -> None:
        """Create a call for `floor` placed at time `placed_at`."""
        self.floor = floor
        self.placed_at = placed_at


class ElevatorCar(Agent, HasEmitters):
    """One car in the bank.

    The car's kinematics are two chained continuous states, as in the tram
    example: ``height' = velocity`` and ``velocity' = acceleration``. Every
    transition in a trip is a Threshold crossing, and the limits those
    thresholds watch are Observables, so re-targeting a moving car is only a
    matter of rewriting ``brake_point``: the braking threshold re-solves for the
    new crossing time on its own.

    Attributes:
        acceleration (Observable): Signed acceleration, m/s^2. Positive is up.
        velocity (ContinuousState): Signed speed, m/s. Positive is up.
        height (ContinuousState): Height above the ground floor, m.
        brake_point (Observable): Height at which braking for the current
            target begins. +inf or -inf disarms the braking threshold.
        cruise_up, cruise_down (Observable): Speed limits that arm the coasting
            thresholds for the current travel direction only.
        stop_up, stop_down (Observable): The velocity (0.0) at which the arrival
            thresholds fire, armed for the current travel direction only and
            disarmed with -inf / +inf otherwise.
    """

    acceleration = Observable(fallback_value=0.0)
    velocity = ContinuousState(fallback_value=0.0, rate=lambda a: a.acceleration)
    height = ContinuousState(fallback_value=0.0, rate=lambda a: a.velocity)
    brake_point = Observable(fallback_value=INF)
    cruise_up = Observable(fallback_value=INF)
    cruise_down = Observable(fallback_value=-INF)
    stop_up = Observable(fallback_value=-INF)
    stop_down = Observable(fallback_value=INF)

    # Travelling up: velocity rises to the cruise speed, height rises to the
    # brake point, velocity falls back to zero. Travelling down the same three
    # crossings happen with the signs flipped, so each direction has its own
    # pair of speed thresholds and the brake threshold watches both ways.
    # Threshold names must not collide with the private store of an Observable
    # they read (see the tram example), hence the `_threshold` suffix.
    _cruise_up_threshold = Threshold(
        state=velocity, limit=cruise_up, callback="start_coasting", direction="rising"
    )
    _cruise_down_threshold = Threshold(
        state=velocity,
        limit=cruise_down,
        callback="start_coasting",
        direction="falling",
    )
    _brake_threshold = Threshold(
        state=height, limit=brake_point, callback="brake", direction="crossing"
    )
    _stop_up_threshold = Threshold(
        state=velocity, limit=stop_up, callback="arrive", direction="falling"
    )
    _stop_down_threshold = Threshold(
        state=velocity, limit=stop_down, callback="arrive", direction="rising"
    )

    def __init__(
        self,
        model: Model,
        floor_height: float = 3.5,
        max_speed: float = 2.5,
        acceleration_rate: float = 1.0,
        door_time: float = 8.0,
        start_floor: int = 0,
    ) -> None:
        """Create a car parked at `start_floor`.

        Args:
            model (Model): The model that owns the car.
            floor_height (float, optional): Distance between floors, m.
            max_speed (float, optional): Cruise speed, m/s.
            acceleration_rate (float, optional): Acceleration and braking
                rate, m/s^2.
            door_time (float, optional): Seconds spent at a floor with the
                doors open before the car is free again.
            start_floor (int, optional): Floor the car starts on.
        """
        super().__init__(model)
        self.floor_height = floor_height
        self.max_speed = max_speed
        self.acceleration_rate = acceleration_rate
        self.door_time = door_time

        self.target_floor: int | None = None
        self.doors_open = False
        self.served = 0

        # The limits the thresholds read must exist before the first
        # ContinuousState assignment, which is what binds the thresholds.
        self.brake_point = INF
        self.cruise_up = INF
        self.cruise_down = -INF
        self.stop_up = -INF
        self.stop_down = INF

        self.acceleration = 0.0
        self.velocity = 0.0
        self.height = start_floor * floor_height

    # --- read-only helpers -------------------------------------------------

    @property
    def idle(self) -> bool:
        """True when the car has no target and its doors are closed."""
        return self.target_floor is None and not self.doors_open

    @property
    def moving(self) -> bool:
        """True while the car is travelling between floors."""
        return self.target_floor is not None and not self.doors_open

    @property
    def direction(self) -> int:
        """+1 travelling up, -1 travelling down, 0 when stopped."""
        if self.velocity > 0 or (self.velocity == 0 and self.acceleration > 0):
            return 1
        if self.velocity < 0 or (self.velocity == 0 and self.acceleration < 0):
            return -1
        return 0

    @property
    def floor(self) -> float:
        """Current height expressed in floors (fractional while moving)."""
        return self.height / self.floor_height

    def height_of(self, floor: int) -> float:
        """Height of `floor` above the ground floor."""
        return floor * self.floor_height

    def distance_to(self, floor: int) -> float:
        """Straight-line distance from the car to `floor`, in meters."""
        return abs(self.height_of(floor) - self.height)

    def can_stop_at(self, floor: int) -> bool:
        """Whether a cruising car can still come to rest exactly at `floor`.

        The car must be coasting at cruise speed, the floor must lie ahead in
        the direction of travel, and the distance left to it must exceed the
        braking distance from the current speed. Cars that are still
        accelerating are left alone: rewriting a threshold limit while the
        watched state has a non-zero second-order rate is mis-projected by
        Mesa's current `Threshold.recalculate` (fix in mesa/mesa#4091), and
        the cruising case is the common one anyway.
        """
        if not self.moving or self.acceleration != 0.0:
            return False
        remaining = (self.height_of(floor) - self.height) * self.direction
        braking = self.velocity**2 / (2.0 * self.acceleration_rate)
        return remaining > braking + 1e-9

    # --- trip planning -----------------------------------------------------

    def peak_speed(self, distance: float) -> float:
        """Top speed reached on a trip of `distance` meters from rest.

        A long trip reaches the cruise speed; a short one is triangular and
        turns around at ``sqrt(a * d)`` with equal acceleration and braking.
        """
        return min(self.max_speed, math.sqrt(self.acceleration_rate * distance))

    def go_to(self, floor: int) -> None:
        """Start, or re-plan, a trip to `floor`.

        Called for a car at rest to depart, and for a moving car whenever a new
        call appears ahead of it that it can still stop for. In the second case
        only ``brake_point`` changes, and the braking threshold re-solves itself
        for the new height.
        """
        target = self.height_of(floor)
        if not self.moving and abs(target - self.height) < 1e-9:
            # Called from the floor the car is already on: just open the doors.
            self.target_floor = floor
            self.model.schedule_event(self.arrive, after=0.0)
            return

        direction = 1 if target > self.height else -1
        distance = abs(target - self.height)
        was_moving = self.moving
        self.target_floor = floor

        if was_moving:
            # Re-targeting on the fly: the car is cruising (see can_stop_at), so
            # it brakes from its current speed. Moving the brake point is all it
            # takes; the braking threshold re-solves itself.
            braking = self.velocity**2 / (2.0 * self.acceleration_rate)
            self.brake_point = target - direction * braking
            return

        peak = self.peak_speed(distance)
        self.brake_point = target - direction * peak**2 / (2.0 * self.acceleration_rate)
        if direction > 0:
            self.cruise_up = self.max_speed
            self.stop_up = 0.0
        else:
            self.cruise_down = -self.max_speed
            self.stop_down = 0.0
        self.acceleration = direction * self.acceleration_rate

    # --- threshold callbacks ------------------------------------------------

    def start_coasting(self) -> None:
        """Hold the cruise speed."""
        self.acceleration = 0.0

    def brake(self) -> None:
        """Decelerate towards the target floor."""
        self.brake_point = INF if self.direction > 0 else -INF
        self.acceleration = -self.direction * self.acceleration_rate

    def arrive(self) -> None:
        """Come to rest at the target floor and open the doors."""
        floor = self.target_floor
        self.acceleration = 0.0
        self.velocity = 0.0
        self.height = self.height_of(floor)
        self.cruise_up, self.cruise_down = INF, -INF
        self.stop_up, self.stop_down = -INF, INF
        self.target_floor = None
        self.doors_open = True
        self.served += self.model.calls_answered(self, floor)
        self.model.schedule_event(self.close_doors, after=self.door_time)

    def close_doors(self) -> None:
        """Close the doors and ask the dispatcher for the next job."""
        self.doors_open = False
        self.model.car_available(self)
