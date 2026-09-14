"""Agents for the Thermostat House model."""

from mesa import Agent
from mesa.experimental.mesa_signals import HasEmitters, Observable, ObservableSignals
from mesa.experimental.states import ContinuousState, Threshold

HEAT_RATE = 0.25  # degrees per time unit while the heater runs
COOL_RATE = -0.15  # degrees per time unit while the house drifts toward outside


class Room(Agent, HasEmitters):
    """A single room whose temperature follows a hysteresis thermostat.

    The temperature is a `ContinuousState` extrapolated analytically between
    events; heating and cooling are just its rate of change. Two `Threshold`s
    compute when the temperature will cross the thermostat's limits and
    schedule exactly one event there, so nothing here steps or polls.

    The limits themselves are `Observable`s - they are the dials. A
    `Threshold` subscribes to its limit and re-arms the projected crossing
    whenever the dial moves, which is the reactive-limits mechanism: changing
    `heat_on_temp` or `heat_off_temp` mid-run needs no call from this agent.

    The one thing that does need a call is a dial jump that lands the
    temperature OUTSIDE the new deadband with no crossing back toward it in
    sight: a threshold only fires on a crossing, and the temperature may be
    cooling away from a raised on-limit with nothing scheduled. `_rearm`
    corrects exactly that state, immediately, on the same dial change.

    Attributes:
        temperature (ContinuousState): Room temperature, degrees.
        temperature_change_rate (Observable): Current rate of change, degrees
            per time unit. Positive while heating, negative while cooling.
        heater_on (Observable): Whether the heater is running.
        heat_on_temp (Observable): The dial that turns the heater on on the
            way down.
        heat_off_temp (Observable): The dial that turns the heater off on the
            way up.
    """

    temperature = ContinuousState(
        fallback_value=20.0, rate=lambda a: a.temperature_change_rate
    )
    temperature_change_rate = Observable(fallback_value=HEAT_RATE)
    heater_on = Observable(fallback_value=True)
    heat_on_temp = Observable(fallback_value=20.5)
    heat_off_temp = Observable(fallback_value=21.5)

    _heat_off_threshold = Threshold(
        state=temperature,
        limit=heat_off_temp,
        callback="stop_heating",
        direction="rising",
    )
    _heat_on_threshold = Threshold(
        state=temperature,
        limit=heat_on_temp,
        callback="start_heating",
        direction="falling",
    )

    def __init__(
        self,
        model,
        temperature: float = 20.0,
        heat_on_temp: float = 20.5,
        heat_off_temp: float = 21.5,
        heating_rate: float = HEAT_RATE,
        cooling_rate: float = COOL_RATE,
    ) -> None:
        """Create the room.

        Args:
            model: The model instance that contains the room.
            temperature: Initial temperature, degrees. Defaults to 20.0.
            heat_on_temp: Dial that turns the heater on on the way down,
                degrees. Defaults to 20.5.
            heat_off_temp: Dial that turns the heater off on the way up,
                degrees. Defaults to 21.5.
            heating_rate: Temperature rise per time unit while heating,
                degrees. Defaults to HEAT_RATE.
            cooling_rate: Temperature drop per time unit while cooling,
                degrees. Defaults to COOL_RATE.
        """
        super().__init__(model)

        self.heating_rate = heating_rate
        self.cooling_rate = cooling_rate

        # The limits the thresholds read must exist before the first
        # ContinuousState assignment, which is what binds the thresholds.
        self.heat_on_temp = heat_on_temp
        self.heat_off_temp = heat_off_temp

        # The heater starts in whichever state the dials demand: below the
        # on-limit it must already be running, above the off-limit it must
        # already be off.
        self.heater_on = temperature < self.heat_on_temp
        self.temperature_change_rate = (
            self.heating_rate if self.heater_on else self.cooling_rate
        )
        self.temperature = temperature

        # Reactive dials: the thresholds re-arm themselves when the limits
        # change (states.py subscribes each Threshold to its limit). `_rearm`
        # handles the one thing a crossing threshold cannot: a jump that
        # strands the temperature outside the new deadband.
        self.observe("heat_on_temp", ObservableSignals.CHANGED, self._rearm)
        self.observe("heat_off_temp", ObservableSignals.CHANGED, self._rearm)

    def _rearm(self, _message=None) -> None:
        """Correct a heater stranded outside the new deadband by a dial jump.

        A threshold only fires on a *crossing*, so a jump can leave the
        temperature outside the new deadband with no crossing back toward it
        in sight. A real thermostat does not wait for that: it turns the
        heater on if the room is below the on-limit and off if it is above
        the off-limit, immediately.
        """
        if self.temperature <= self.heat_on_temp and not self.heater_on:
            self.start_heating()
        elif self.temperature >= self.heat_off_temp and self.heater_on:
            self.stop_heating()

    def stop_heating(self) -> None:
        """Turn the heater off and let the room cool toward the outside."""
        self.heater_on = False
        self.temperature_change_rate = self.cooling_rate

    def start_heating(self) -> None:
        """Turn the heater on and start warming the room."""
        self.heater_on = True
        self.temperature_change_rate = self.heating_rate
