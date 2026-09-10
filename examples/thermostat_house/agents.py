"""Agents for the Thermostat House model."""

from mesa import Agent
from mesa.experimental.mesa_signals import HasEmitters, Observable, ObservableSignals
from mesa.experimental.states import ContinuousState, Threshold

HEAT_RATE = 0.25  # °C per time unit while the heater runs
COOL_RATE = -0.15  # °C per time unit while the house drifts toward outside


class Room(Agent, HasEmitters):
    """A single room whose temperature follows a hysteresis thermostat.

    The temperature is a `ContinuousState` extrapolated analytically between
    events; heating and cooling are just its rate of change. Two `Threshold`s
    compute when the temperature will cross the thermostat's limits and
    schedule exactly one event there, so nothing here steps or polls.

    The limits are `Observable`s fed from the setpoint and the deadband. A
    Threshold reading an Observable re-arms itself when the limit changes, so
    turning the dial during a run is picked up without any explicit call.

    Attributes:
        temperature (ContinuousState): Room temperature, °C.
        temperature_change_rate (Observable): Current rate of change, °C per time
            unit. Positive while heating, negative while cooling.
        heater_on (Observable): Whether the heater is running.
        setpoint (Observable): Target temperature, °C.
        hysteresis (Observable): Half-width of the deadband around the
            setpoint, °C.
        heat_on_temp (Observable): Limit that turns the heater on on the way
            down (setpoint - hysteresis).
        heat_off_temp (Observable): Limit that turns the heater off on the way
            up (setpoint + hysteresis).
    """

    temperature = ContinuousState(
        fallback_value=20.0, rate=lambda a: a.temperature_change_rate
    )
    temperature_change_rate = Observable(fallback_value=HEAT_RATE)
    heater_on = Observable(fallback_value=True)
    setpoint = Observable(fallback_value=21.0)
    hysteresis = Observable(fallback_value=0.5)
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
        setpoint: float = 21.0,
        hysteresis: float = 0.5,
        heating_rate: float = HEAT_RATE,
        cooling_rate: float = COOL_RATE,
    ) -> None:
        """Create the room.

        Args:
            model: The model instance that contains the room.
            temperature: Initial temperature, °C. Defaults to 20.0.
            setpoint: Target temperature, °C. Defaults to 21.0.
            hysteresis: Half-width of the deadband around the setpoint, °C.
                Defaults to 0.5.
            heating_rate: Temperature rise per time unit while heating, °C.
                Defaults to HEAT_RATE.
            cooling_rate: Temperature drop per time unit while cooling, °C.
                Defaults to COOL_RATE.
        """
        super().__init__(model)

        self.heating_rate = heating_rate
        self.cooling_rate = cooling_rate
        self.setpoint = setpoint
        self.hysteresis = hysteresis

        # The limits the thresholds read must exist before the first
        # ContinuousState assignment, which is what binds the thresholds.
        self._match_dials()

        # The heater starts in whichever state the dials demand: below the
        # on-limit it must already be running, above the off-limit it must
        # already be off.
        self.heater_on = temperature < self.heat_on_temp
        self.temperature_change_rate = (
            self.heating_rate if self.heater_on else self.cooling_rate
        )
        self.temperature = temperature

        # Reactive dials: moving the setpoint or the deadband writes new
        # limits, and the thresholds re-arm themselves from those Observables
        # while `_rearm` corrects the heater if the jump stranded it.
        self.observe("setpoint", ObservableSignals.CHANGED, self._rearm)
        self.observe("hysteresis", ObservableSignals.CHANGED, self._rearm)

    def _match_dials(self, _message=None) -> None:
        """Rewrite the threshold limits from the setpoint and deadband.

        Called on every dial change; the thresholds observe their limits and
        re-arm themselves from what this writes.
        """
        self.heat_on_temp = self.setpoint - self.hysteresis
        self.heat_off_temp = self.setpoint + self.hysteresis

    def _rearm(self, _message=None) -> None:
        """React to a dial change: update the limits and correct any mismatch.

        A threshold only fires on a *crossing*, so a setpoint jump can leave
        the temperature outside the new deadband with no crossing back toward
        it in sight. A real thermostat does not wait for that: it turns the
        heater on if the room is below the on-limit and off if it is above
        the off-limit, immediately.
        """
        self._match_dials()
        if self.temperature <= self.heat_on_temp:
            if not self.heater_on:
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
