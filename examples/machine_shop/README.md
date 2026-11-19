# Machine Shop: Production and Breakdowns

This experimental example demonstrates Mesa's Actions API using a small machine-shop simulation.

## Scenario

A machine starts a production job. During production, the machine breaks down twice. Each breakdown interrupts the production action and starts a repair action. Once repair finishes, the machine resumes the interrupted production job from its saved progress rather than restarting it.

## Concepts demonstrated

- `Action`: production and repair are represented as timed actions.
- `HasActions`: the machine can manage and start actions.
- Interruption: repair interrupts an in-progress production action.
- Priority: repair has higher priority than production.
- Progress preservation: production resumes from the progress reached before the breakdown.
- Resumption: the machine starts the interrupted production action again after repair.

## Example timeline

| Simulation time | Event |
|---:|---|
| 0 | Production starts |
| 4 | First breakdown; production is interrupted at 40% |
| 4–7 | Repair runs |
| 7 | Production resumes at 40% |
| 9 | Second breakdown; production is interrupted at 60% |
| 9–12 | Repair runs |
| 12 | Production resumes at 60% |
| 16 | Production completes |

## Running the example

Install a Mesa version that includes the experimental Actions API (for example the current `main` branch) together with Solara (`pip install solara`), then run this from the example folder:

```bash
solara run app.py
```

Open the local URL printed by Solara in your browser. Use the **▶ / ❚❚** button to start and pause automatic playback, **Step** to advance one time unit at a time, and **Reset** to restart the simulation.

## Version note

This example uses Mesa's experimental Actions API, which may change. It was developed against Mesa commit `fe24c24e` (`fe24c24ee34762de2ff85d487af14bfb5cd1dbb2`).