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
        initial_temperature: Temperature of the room at t=0, degrees.
        heat_on_temp: Dial that turns the heater on on the way down, degrees.
        heat_off_temp: Dial that turns the heater off on the way up, degrees.
        heating_rate: Temperature rise per time unit while heating, degrees.
        cooling_rate: Temperature drop per time unit while cooling, degrees.
    """

    initial_temperature: float = 20.0
    heat_on_temp: float = 20.5
    heat_off_temp: float = 21.5
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
            heat_on_temp=scenario.heat_on_temp,
            heat_off_temp=scenario.heat_off_temp,
            heating_rate=scenario.heating_rate,
            cooling_rate=scenario.cooling_rate,
        )

        self.datacollector = DataCollector(
            model_reporters={
                "Temperature": lambda m: m.room.temperature,
                "Heat On": lambda m: m.room.heat_on_temp,
                "Heat Off": lambda m: m.room.heat_off_temp,
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
        f"initial_temperature={model.room.temperature:.1f}, "
        f"heat_on_temp={model.room.heat_on_temp:.1f}, "
        f"heat_off_temp={model.room.heat_off_temp:.1f}\n"
    )

    model.run_for(50.0)

    df = model.datacollector.get_model_vars_dataframe()
    print(df.to_string())

    # The temperature must stay inside the deadband once the room has warmed
    # into it: the thermostat holds it between heat_on_temp and heat_off_temp.
    # The first two samples are the cold start, where the room begins below
    # the band and warms in.
    low = model.room.heat_on_temp
    high = model.room.heat_off_temp
    in_band = np.all(
        (df["Temperature"].iloc[2:] >= low - 1e-9)
        & (df["Temperature"].iloc[2:] <= high + 1e-9)
    )
    print(f"\nFinal time:     {model.time:.2f}")
    print(f"Final temperature: {model.room.temperature:.2f}")
    print(f"Heater:        {'on' if model.room.heater_on else 'off'}")
    print(f"Temperature stayed inside [{low:.2f}, {high:.2f}]: {in_band}")
    assert in_band
