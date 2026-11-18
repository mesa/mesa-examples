# Bus Line Model (Continuous States and Actions Example)

## Summary

A bus runs a loop of stops while passengers arrive at random and board through its door. The model combines Mesa's two experimental toolkits for event-driven behaviour: continuous states and thresholds for the bus's motion, and timed, interruptible actions for boarding.

**The bus** moves the way the tram in Mesa's [Tram Route Model](https://github.com/mesa/mesa/tree/main/mesa/examples/experimental/tram_model) does. Its `speed` and `position` are `ContinuousState`s, and every change of motion is a `Threshold` crossing: it accelerates away from a stop, coasts at cruise speed, brakes at a point solved from the segment's peak speed, and arrives when its speed falls to zero. At each stop it opens its doors for a fixed dwell time, and when that time is up it leaves, whether or not everyone has boarded.

**Passengers** arrive at each stop as a Poisson stream, each arrival scheduling the next one. Boarding is an `Action` that takes a fixed time per passenger, and only one passenger fits through the door at a time:

```python
class Board(Action):
    def __init__(self, passenger, bus, duration):
        super().__init__(
            passenger,
            duration=duration,
            completion_requirements=lambda p: bus.doors_open_at == p.origin,
        )
```

When a boarding completes, the next waiting passenger steps into the door. When the dwell time runs out, the bus interrupts the passenger in the door (`on_interrupt` puts them back in the queue) and everyone still waiting is left behind until the next lap. The completion requirement re-checks that the doors are open when the boarding time is up, so a boarding that ends at the very moment the bus leaves does not count.

This makes the trade-off at the heart of bus scheduling visible: a short dwell keeps the bus moving but leaves passengers behind at busy stops, and a long one carries more passengers per lap but makes every lap slower. Try the dwell time, boarding time and arrival rate sliders and watch the "Left behind" curve.

As in the tram model, the model's `step` only samples data for the plots. The bus and the passengers need no per-step logic: motion is extrapolated analytically, transitions fire from thresholds, and boarding completes or is interrupted on the event queue.

## How to Run

Install Mesa with recommended dependencies:

```
pip install -U --pre "mesa[rec]"
```

Then run the example:

```
solara run app.py
```

Open the displayed local URL in your browser.

To run the model for half an hour of simulated time without visualization:

```
python model.py
```

## Files

* `model.py`: The `BusLine` model and its `BusLineScenario`.
* `agents.py`: The `Bus` agent with its continuous states and thresholds, the `Passenger` agent, and the `Board` action.
* `app.py`: The interactive visualization.

## Further Reading

The continuous states and thresholds live in `mesa.experimental.states`, and the actions in `mesa.experimental.actions`. Both are experimental and can change without deprecation. This example was built against Mesa `main` at commit `e988375` (2026-11-10).
