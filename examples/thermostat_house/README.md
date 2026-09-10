# Thermostat House

A house with one room under hysteresis thermostat control, built entirely on
Mesa's experimental continuous-time APIs.

## Summary

The room temperature is a `ContinuousState`: it stores a base value and a
rate of change, and extrapolates the current value whenever it is read. Two
`Threshold`s watch it analytically - the heater comes on when the temperature
falls to `heat_on_temp` and goes off when it rises to `heat_off_temp`. Each
crossing is computed in advance and scheduled as exactly one event on the
model's event queue, so the room never steps or polls: the only `step()` in
the model samples data for the plots.

The dials are `Observable`s, and the limits the thresholds watch *are* those
dials. `Threshold` subscribes to its limit observable, so dragging either
slider mid-run re-arms the projected crossing automatically - no call from
the room is involved, which is the reactive-limits mechanism this example
exists to show (the same one the tram's brake point uses).

One edge is handled explicitly: a threshold only fires on a crossing, so a
dial jump can land the temperature outside the new deadband with no crossing
back toward it in sight (the room is cooling away from a raised on-limit, for
example). The room corrects that state on the same dial change by turning the
heater on or off immediately.

### Mesa experimental APIs demonstrated

| Feature | Usage |
|---|---|
| `ContinuousState` | Room temperature stored as base value + rate, extrapolated analytically |
| `Threshold` | Exact, analytically computed crossing times for heating on/off events |
| Reactive limits | `Threshold` re-arms itself when its limit `Observable` changes, so the dials are live |
| `Observable` | Heater state, temperature rate and the two dials as signal-emitting fields |
| `Scenario` | Model parameters (`heat_on_temp`, `heat_off_temp`, rates) as a typed scenario |

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

The temperature swinging between the dials, the two dials as guide lines, and
the heater's on/off state.

## Files

| File | Description |
|---|---|
| `agents.py` | `Room` agent: temperature state, thermostat thresholds, heater |
| `model.py` | `ThermostatHouse` model |
| `app.py` | Solara visualization |

This example builds against Mesa main (commit `a5dfcd6`, 2026-09-08); the
`mesa.experimental.*` APIs are pre-release and may change without deprecation.