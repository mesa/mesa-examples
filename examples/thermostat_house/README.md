# Thermostat House

A house with one room under hysteresis thermostat control, built entirely on
Mesa's experimental continuous-time APIs.

## Summary

The room temperature is a `ContinuousState`: it stores a base value and a
rate of change, and extrapolates the current value whenever it is read. Two
`Threshold`s watch it analytically - the heater comes on when the temperature
falls to `setpoint - hysteresis` and goes off when it rises to
`setpoint + hysteresis`. Each crossing is computed in advance and scheduled
as exactly one event on the model's event queue, so the room never steps or
polls: the only `step()` in the model samples data for the plots.

The thermostat is fully reactive. The limits are `Observable`s derived from
the setpoint and deadband, so dragging the setpoint slider mid-run rewrites
the limits and the thresholds re-arm themselves without any explicit call.

### Mesa experimental APIs demonstrated

| Feature | Usage |
|---|---|
| `ContinuousState` | Room temperature stored as base value + rate, extrapolated analytically |
| `Threshold` | Exact, analytically computed crossing times for heating on/off events |
| Reactive limits | Thresholds bound to `Observable` limits re-arm when the dials move |
| `Observable` | Heater state, temperature rate and thermostat dials as signal-emitting fields |
| `Scenario` | Model parameters (`setpoint`, `hysteresis`, rates) as a typed scenario |

## How to run

```bash
pip install "mesa @ git+https://github.com/mesa/mesa@main"
python model.py
```

Runs the simulation for 50 time units, prints the sampled temperature series
and asserts the temperature stayed inside the deadband throughout.

## Visualisation

```bash
python -m solara run app.py
```

Two lines and a status readout: the temperature swinging between the dials,
the setpoint, and the heater's on/off state.

## Files

| File | Description |
|---|---|
| `agents.py` | `Room` agent: temperature state, thermostat thresholds, heater |
| `model.py` | `ThermostatHouse` model |
| `app.py` | Solara visualization |

This example builds against Mesa main (commit `a5dfcd6`, 2026-09-08); the
`mesa.experimental.*` APIs are pre-release and may change without deprecation.