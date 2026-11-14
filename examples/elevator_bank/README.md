# Elevator Bank

A bank of elevator cars answering hall calls in a building, built on Mesa's experimental continuous states and run entirely in continuous time.

## Summary
Each car has two chained continuous states, `height' = velocity` and `velocity' = acceleration`, exactly like the tram in Mesa's own `tram_model` example. A trip is three analytically solved Threshold crossings: the velocity reaches the cruise speed (start coasting), the height reaches the brake point (start braking), the velocity returns to zero (open the doors). Nothing is polled per tick; `step()` only samples data for the plots and can be deleted without changing a single event time.

What this example adds over the tram is **reactive re-targeting**. Hall calls arrive as events on random floors. When a call lands on a floor ahead of a cruising car that can still stop there, the dispatcher sends that car to the new floor by rewriting its `brake_point` Observable. The braking Threshold re-solves itself for the new height, the car stops at the nearer floor, and the floor it was originally heading for stays in the queue and is picked up afterwards. Calls on a floor no car can take wait in a FIFO queue and are handed to the next car that closes its doors.

### Mesa features demonstrated

| Feature | Usage |
|---|---|
| `ContinuousState` (chained) | `velocity` driven by `acceleration`, `height` driven by `velocity` |
| `Threshold` with `Observable` limits | Cruise, brake and arrival thresholds, armed and disarmed per travel direction by rewriting their limits (`±inf` disarms) |
| Reactive limits | Re-targeting a moving car = assigning a new `brake_point`; no re-arming calls |
| `schedule_event(after=...)` | Door closing, stochastic hall calls |
| `run_until` | Running the pure event-driven model to a target time |
| `Scenario` | Typed model parameters with a seed (`ElevatorScenario`) |
| `DataRecorder` + `track_agents` | Recording every car's height, velocity and acceleration |

## How to run
```bash
python model.py
```
Runs one hour of simulated time with two cars on twelve floors and prints how many calls were placed and answered, the mean wait, and where each car ended up.

```bash
solara run app.py
```
Opens the interactive app: a shaft view with each car at its current height and the floors with a waiting call marked, plus plots of the queue length and mean wait. Floors, cars, cruise speed, acceleration, door time and call rate are sliders.

## Files

| File | Description |
|---|---|
| `agents.py` | `ElevatorCar` (continuous states, thresholds, trip planning) and `Call` |
| `model.py` | `ElevatorBank` model and `ElevatorScenario`, with the dispatcher |
| `app.py` | Solara visualisation |

## Notes
- Acceleration and braking share one rate, so a short trip has a triangular speed profile that peaks at `sqrt(a·d)`; a long one cruises at `max_speed`.
- Only cruising cars are re-targeted. Rewriting a threshold limit while the watched state still has a non-zero second-order rate (a car that is accelerating) is mis-projected by Mesa's current `Threshold.recalculate`; a fix is proposed in [mesa/mesa#4091](https://github.com/mesa/mesa/pull/4091), after which the restriction can go.
- Requires a Mesa build with `mesa.experimental.states` (Mesa 4.0 development versions).
