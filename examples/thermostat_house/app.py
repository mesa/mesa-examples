"""Solara app for the Thermostat House model.

Run with ``solara run app.py`` from this directory.
"""

import solara
from mesa.visualization import Slider, SolaraViz, make_plot_component

try:
    from .model import ThermostatHouse, ThermostatScenario
except ImportError:
    from model import ThermostatHouse, ThermostatScenario

TemperaturePlot = make_plot_component({"Temperature": "#E4572E", "Setpoint": "#17BEBB"})
HeaterPlot = make_plot_component({"Heater": "#FFC914"})


@solara.component
def thermostat_view(model):
    """Show the current temperature and heater state."""
    return solara.Markdown(
        f"**t = {model.time:.2f}**  ·  temperature = {model.room.temperature:.2f} °C  ·  "
        f"heater {'on' if model.room.heater_on else 'off'}"
    )


model_params = {
    "rng": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "initial_temperature": Slider("Initial temperature (°C)", 20, 0, 40, 1),
    "setpoint": Slider("Setpoint (°C)", 21, 15, 28, 0.5),
    "hysteresis": Slider("Deadband half-width (°C)", 0.5, 0.1, 2.0, 0.1),
}


model = ThermostatHouse(scenario=ThermostatScenario())

page = SolaraViz(
    model,
    components=[thermostat_view, TemperaturePlot, HeaterPlot],
    model_params=model_params,
    name="Thermostat House",
)
page  # noqa
