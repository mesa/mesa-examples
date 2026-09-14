"""Solara app for the Thermostat House model.

Run with ``solara run app.py`` from this directory.
"""

import solara
from mesa.visualization import Slider, SolaraViz, make_plot_component

try:
    from .model import ThermostatHouse, ThermostatScenario
except ImportError:
    from model import ThermostatHouse, ThermostatScenario

TemperaturePlot = make_plot_component(
    {"Temperature": "#E4572E", "Heat On": "#17BEBB", "Heat Off": "#17BEBB"}
)
HeaterPlot = make_plot_component({"Heater": "#FFC914"})


@solara.component
def thermostat_view(model):
    """Show the current temperature and heater state."""
    return solara.Markdown(
        f"**t = {model.time:.2f}**  ·  temperature = {model.room.temperature:.2f}  ·  "
        f"heater {'on' if model.room.heater_on else 'off'}"
    )


model_params = {
    "rng": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "initial_temperature": Slider("Initial temperature", 20, 0, 40, 1),
    "heat_on_temp": Slider("Heater on below", 20.5, 15.0, 28.0, 0.5),
    "heat_off_temp": Slider("Heater off above", 21.5, 15.0, 28.0, 0.5),
}


model = ThermostatHouse(scenario=ThermostatScenario())

page = SolaraViz(
    model,
    components=[thermostat_view, TemperaturePlot, HeaterPlot],
    model_params=model_params,
    name="Thermostat House",
)
page  # noqa
