"""Thermostat House model.

A single room whose temperature is kept inside a deadband around a target by
a hysteresis thermostat, built entirely on Mesa's experimental continuous
states. The temperature is extrapolated analytically and the thermostat's
turn-on/turn-off events are scheduled exactly when the temperature crosses
the dials -- there is no step logic at all; `step()` only samples data for
plotting and can be deleted without changing the temperature curve.
"""

from mesa import Model
from mesa.datacollection import DataCollector
from mesa.experimental.scenarios import Scenario

try:
    from .agents import Room
except ImportError:
    from agents import Room


class ThermostatScenario(Scenario):
    """Scenario for the Thermostat House model.

    Args:
        initial_temperature: Temperature of the room at t=0, °C.
        setpoint: Target temperature, °C.
        hysteresis: Half-width of the deadband around the setpoint, °C.
        heating_rate: Temperature rise per time unit while heating, °C.
        cooling_rate: Temperature drop per time unit while cooling, °C.
    """

    initial_temperature: float = 20.0
    setpoint: float = 21.0
    hysteresis: float = 0.5
    heating_rate: float = 0.25
    cooling_rate: float = -0.15


class ThermostatHouse(Model):
    """A house with one room under thermostat control.

    Attributes:
        room (Room): The room and its heating plant.
    """

    def __init__(self, scenario: ThermostatScenario = ThermostatScenario):
        """Create the model and its room.

        Args:
            scenario: ThermostatScenario containing the model parameters.
        """
        super().__init__(scenario=scenario)

        self.room = Room(
            self,
            temperature=scenario.initial_temperature,
            setpoint=scenario.setpoint,
            hysteresis=scenario.hysteresis,
            heating_rate=scenario.heating_rate,
            cooling_rate=scenario.cooling_rate,
        )

        self.datacollector = DataCollector(
            model_reporters={
                "Temperature": lambda m: m.room.temperature,
                "Setpoint": lambda m: m.room.setpoint,
                "Heater": lambda m: 1.0 if m.room.heater_on else 0.0,
            }
        )
        self.datacollector.collect(self)

    def step(self) -> None:
        """Sample the temperature once per time unit.

        The room needs no per-step logic: its temperature is extrapolated
        analytically and the heater flips from analytically computed event
        times on the event queue. This step exists purely to feed the
        DataCollector behind the plots.
        """
        self.datacollector.collect(self)


if __name__ == "__main__":
    import numpy as np

    model = ThermostatHouse()

    print(
        f"initial_temperature={model.room.temperature:.1f} °C, "
        f"setpoint={model.room.setpoint:.1f} °C, "
        f"hysteresis={model.room.hysteresis:.1f} °C\n"
    )

    model.run_for(50.0)

    df = model.datacollector.get_model_vars_dataframe()
    print(df.to_string())

    # The temperature must stay inside the deadband once the room has warmed
    # into it: the thermostat holds it between setpoint - hysteresis and
    # setpoint + hysteresis. The first two samples are the cold start, where
    # the room begins below the band and warms in.
    low = model.room.setpoint - model.room.hysteresis
    high = model.room.setpoint + model.room.hysteresis
    in_band = np.all(
        (df["Temperature"].iloc[2:] >= low - 1e-9)
        & (df["Temperature"].iloc[2:] <= high + 1e-9)
    )
    print(f"\nFinal time:     {model.time:.2f}")
    print(f"Final temperature: {model.room.temperature:.2f} °C")
    print(f"Heater:        {'on' if model.room.heater_on else 'off'}")
    print(f"Temperature stayed inside [{low:.2f}, {high:.2f}] °C: {in_band}")
    assert in_band
